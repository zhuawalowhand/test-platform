"""
定时任务调度器
使用 APScheduler 根据 cron 表达式自动执行测试任务并发送 Webhook 通知
"""
import json
import logging
import asyncio
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .database import SessionLocal
from .models import ScheduledTask, TestCase, TestResult, TestReport, Environment
from .executor import execute_single_testcase
from .webhook import send_webhook_notification

logger = logging.getLogger(__name__)

# 全局调度器实例
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


def _parse_cron(cron_expr: str) -> dict:
    """
    解析 5 字段 cron 表达式: 分 时 日 月 周
    例: "0 0 * * *" → {"minute": "0", "hour": "0", "day": "*", "month": "*", "day_of_week": "*"}
    """
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        raise ValueError(f"无效的 cron 表达式 '{cron_expr}'，需要 5 个字段：分 时 日 月 周")
    return {
        "minute": parts[0],
        "hour": parts[1],
        "day": parts[2],
        "month": parts[3],
        "day_of_week": parts[4],
    }


def _job_id(task_id: int) -> str:
    return f"scheduled_task_{task_id}"


async def _execute_scheduled_task(task_id: int):
    """
    调度器回调：执行指定定时任务的所有用例
    独立于 HTTP 请求运行，自行管理 DB session
    """
    db = SessionLocal()
    try:
        # 1. 获取任务配置
        task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        if not task or not task.enabled:
            logger.info(f"任务 {task_id} 不存在或已禁用，跳过")
            return

        logger.info(f"[调度器] 开始执行任务: {task.name} (ID={task_id})")

        # 2. 解析用例 ID
        try:
            case_ids = json.loads(task.testcase_ids or "[]")
        except:
            case_ids = []

        # 3. 获取用例
        query = db.query(TestCase).filter(TestCase.owner_id == task.owner_id)
        if case_ids:
            query = query.filter(TestCase.id.in_(case_ids))
        testcases = query.order_by(TestCase.sort_order.asc(), TestCase.id.asc()).all()

        if not testcases:
            logger.warning(f"[调度器] 任务 {task.name} 没有可执行的用例")
            return

        # 4. 获取环境
        environment = None
        env_name = None
        if task.environment_id:
            environment = db.query(Environment).filter(
                Environment.id == task.environment_id
            ).first()
            if environment:
                env_name = environment.name

        # 5. 创建报告
        report = TestReport(
            name=f"[定时] {task.name}",
            total=len(testcases),
            environment=env_name,
            owner_id=task.owner_id
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        # 6. 逐条执行
        passed_count = 0
        failed_count = 0
        total_duration = 0

        for testcase in testcases:
            result_data = await execute_single_testcase(testcase, environment)
            test_result = TestResult(
                testcase_id=testcase.id,
                report_id=report.id,
                passed=result_data["passed"],
                actual_status=result_data["actual_status"],
                expected_status=testcase.expected_status,
                response_body=result_data["response_body"],
                duration_ms=result_data["duration_ms"],
                error_message=result_data["error_message"],
                assertion_results=result_data.get("assertion_results")
            )
            db.add(test_result)
            if result_data["passed"]:
                passed_count += 1
            else:
                failed_count += 1
            total_duration += result_data["duration_ms"]

        # 7. 更新报告和 last_run
        report.passed = passed_count
        report.failed = failed_count
        report.duration_ms = round(total_duration, 2)
        task.last_run = datetime.now(timezone.utc)
        db.commit()
        db.refresh(report)

        pass_rate = (passed_count / report.total * 100) if report.total > 0 else 0
        logger.info(
            f"[调度器] 任务 {task.name} 执行完成: "
            f"{passed_count}/{report.total} 通过, 通过率 {pass_rate:.1f}%"
        )

        # 8. Webhook 通知
        if task.webhook_url:
            result_records = db.query(TestResult).filter(
                TestResult.report_id == report.id
            ).all()
            case_name_map = {tc.id: tc.name for tc in testcases}
            enriched_results = [
                {
                    "testcase_id": r.testcase_id,
                    "testcase_name": case_name_map.get(r.testcase_id, ""),
                    "passed": r.passed,
                    "actual_status": r.actual_status,
                    "error_message": r.error_message,
                }
                for r in result_records
            ]
            report_summary = {
                "name": report.name,
                "total": report.total,
                "passed": report.passed,
                "failed": report.failed,
                "pass_rate": round(pass_rate, 2),
                "duration_ms": report.duration_ms,
                "environment": report.environment,
            }
            result = await send_webhook_notification(
                task.webhook_url, report_summary, enriched_results
            )
            logger.info(f"[调度器] Webhook 通知: {result['message']}")

    except Exception as e:
        logger.error(f"[调度器] 任务 {task_id} 执行异常: {e}", exc_info=True)
    finally:
        db.close()


def add_job(task_id: int, cron_expression: str):
    """添加或更新一个定时任务"""
    try:
        cron_params = _parse_cron(cron_expression)
        trigger = CronTrigger(**cron_params)
        scheduler.add_job(
            _execute_scheduled_task,
            trigger=trigger,
            args=[task_id],
            id=_job_id(task_id),
            replace_existing=True,
            name=f"scheduled_task_{task_id}",
        )
        logger.info(f"[调度器] 已注册任务 {task_id}, cron: {cron_expression}")
    except Exception as e:
        logger.error(f"[调度器] 注册任务 {task_id} 失败: {e}")


def remove_job(task_id: int):
    """移除一个定时任务"""
    job_id = _job_id(task_id)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"[调度器] 已移除任务 {task_id}")


def load_all_jobs():
    """启动时从数据库加载所有启用的任务"""
    db = SessionLocal()
    try:
        tasks = db.query(ScheduledTask).filter(ScheduledTask.enabled == True).all()
        count = 0
        for task in tasks:
            try:
                add_job(task.id, task.cron_expression)
                count += 1
            except Exception as e:
                logger.error(f"[调度器] 加载任务 {task.id} ({task.name}) 失败: {e}")
        logger.info(f"[调度器] 启动完成，已加载 {count}/{len(tasks)} 个任务")
    finally:
        db.close()


def get_jobs_info() -> list:
    """获取当前所有已注册任务的信息"""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger),
        })
    return jobs
