from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json
from datetime import datetime, timezone

from ..database import get_db
from ..models import ScheduledTask, User, TestCase, TestResult, TestReport, Environment
from ..schemas import ScheduledTaskCreate, ScheduledTaskUpdate, ScheduledTaskResponse
from ..auth import get_current_user
from ..executor import execute_single_testcase
from ..webhook import send_webhook_notification

router = APIRouter(prefix="/api/schedules", tags=["定时任务"])


@router.post("/", response_model=ScheduledTaskResponse, summary="创建定时任务")
def create_schedule(
    task: ScheduledTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建定时执行任务"""
    db_task = ScheduledTask(
        name=task.name,
        cron_expression=task.cron_expression,
        testcase_ids=task.testcase_ids or "[]",
        environment_id=task.environment_id,
        webhook_url=task.webhook_url,
        enabled=True,
        owner_id=current_user.id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.get("/", response_model=List[ScheduledTaskResponse], summary="任务列表")
def list_schedules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的所有定时任务"""
    return db.query(ScheduledTask).filter(
        ScheduledTask.owner_id == current_user.id
    ).all()


@router.get("/{task_id}", response_model=ScheduledTaskResponse, summary="任务详情")
def get_schedule(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取定时任务详情"""
    task = db.query(ScheduledTask).filter(
        ScheduledTask.id == task_id,
        ScheduledTask.owner_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.put("/{task_id}", response_model=ScheduledTaskResponse, summary="更新任务")
def update_schedule(
    task_id: int,
    task: ScheduledTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新定时任务"""
    db_task = db.query(ScheduledTask).filter(
        ScheduledTask.id == task_id,
        ScheduledTask.owner_id == current_user.id
    ).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="任务不存在")

    update_data = task.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)

    db.commit()
    db.refresh(db_task)
    return db_task


@router.delete("/{task_id}", summary="删除任务")
def delete_schedule(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除定时任务"""
    db_task = db.query(ScheduledTask).filter(
        ScheduledTask.id == task_id,
        ScheduledTask.owner_id == current_user.id
    ).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="任务不存在")

    db.delete(db_task)
    db.commit()
    return {"message": "删除成功"}


@router.patch("/{task_id}/toggle", response_model=ScheduledTaskResponse, summary="启用/禁用任务")
def toggle_schedule(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """切换定时任务的启用状态"""
    db_task = db.query(ScheduledTask).filter(
        ScheduledTask.id == task_id,
        ScheduledTask.owner_id == current_user.id
    ).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="任务不存在")

    db_task.enabled = not db_task.enabled
    db.commit()
    db.refresh(db_task)
    return db_task


@router.post("/{task_id}/run", summary="立即执行任务")
async def run_schedule_now(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """立即执行定时任务中的所有用例，并触发 Webhook 通知"""
    db_task = db.query(ScheduledTask).filter(
        ScheduledTask.id == task_id,
        ScheduledTask.owner_id == current_user.id
    ).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 解析用例ID
    try:
        case_ids = json.loads(db_task.testcase_ids or "[]")
    except:
        case_ids = []

    # 获取用例
    query = db.query(TestCase).filter(TestCase.owner_id == current_user.id)
    if case_ids:
        query = query.filter(TestCase.id.in_(case_ids))
    testcases = query.order_by(TestCase.sort_order.asc(), TestCase.id.asc()).all()

    if not testcases:
        raise HTTPException(status_code=404, detail="没有找到可执行的用例")

    # 获取环境
    environment = None
    env_name = None
    if db_task.environment_id:
        environment = db.query(Environment).filter(
            Environment.id == db_task.environment_id,
            Environment.owner_id == current_user.id
        ).first()
        if environment:
            env_name = environment.name

    # 创建报告
    report = TestReport(
        name=f"[定时任务] {db_task.name}",
        total=len(testcases),
        environment=env_name,
        owner_id=current_user.id
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # 执行
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

    # 更新报告
    report.passed = passed_count
    report.failed = failed_count
    report.duration_ms = round(total_duration, 2)

    # 更新 last_run
    db_task.last_run = datetime.now(timezone.utc)
    db.commit()
    db.refresh(report)

    pass_rate = (passed_count / report.total * 100) if report.total > 0 else 0

    # Webhook 通知
    if db_task.webhook_url:
        result_records = db.query(TestResult).filter(TestResult.report_id == report.id).all()
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
        import asyncio
        asyncio.create_task(
            send_webhook_notification(db_task.webhook_url, report_summary, enriched_results)
        )

    return {
        "report_id": report.id,
        "name": report.name,
        "total": report.total,
        "passed": report.passed,
        "failed": report.failed,
        "pass_rate": round(pass_rate, 2),
        "duration_ms": report.duration_ms,
        "webhook_sent": bool(db_task.webhook_url)
    }
