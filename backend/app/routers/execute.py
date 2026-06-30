from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import TestCase, TestResult, TestReport, User, Environment
from ..schemas import ExecuteRequest, TestReportResponse, TestReportDetail, TestResultResponse
from ..auth import get_current_user
from ..executor import execute_single_testcase
from ..webhook import send_webhook_notification

router = APIRouter(prefix="/api/execute", tags=["执行与报告"])


@router.post("/", response_model=TestReportDetail, summary="执行测试")
async def execute_tests(
    request: ExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    执行测试用例并生成报告
    - 不传 testcase_ids 则执行当前用户的所有用例
    - 可指定 environment_id 使用特定环境配置
    - 返回完整的测试报告（包含每条用例的执行结果）
    """
    # 获取要执行的用例（按 sort_order 排序）
    query = db.query(TestCase).filter(TestCase.owner_id == current_user.id)
    if request.testcase_ids:
        query = query.filter(TestCase.id.in_(request.testcase_ids))
    testcases = query.order_by(TestCase.sort_order.asc(), TestCase.id.asc()).all()

    if not testcases:
        raise HTTPException(status_code=404, detail="没有找到可执行的用例")

    # 获取环境配置
    environment = None
    env_name = None
    if request.environment_id:
        environment = db.query(Environment).filter(
            Environment.id == request.environment_id,
            Environment.owner_id == current_user.id
        ).first()
        if environment:
            env_name = environment.name

    # 创建报告
    report = TestReport(
        name=request.name or f"测试报告 #{db.query(TestReport).count() + 1}",
        total=len(testcases),
        environment=env_name,
        owner_id=current_user.id
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # 逐条执行
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

    # 更新报告统计
    report.passed = passed_count
    report.failed = failed_count
    report.duration_ms = round(total_duration, 2)
    db.commit()

    # 刷新获取完整数据
    db.refresh(report)
    result_records = db.query(TestResult).filter(TestResult.report_id == report.id).all()

    # 构造返回
    pass_rate = (passed_count / report.total * 100) if report.total > 0 else 0
    response_data = {
        "id": report.id,
        "name": report.name,
        "total": report.total,
        "passed": report.passed,
        "failed": report.failed,
        "duration_ms": report.duration_ms,
        "pass_rate": round(pass_rate, 2),
        "environment": report.environment,
        "created_at": report.created_at,
        "results": result_records
    }

    # Webhook 通知
    if request.webhook_url:
        # 补充用例名称到结果中
        case_name_map = {tc.id: tc.name for tc in testcases}
        enriched_results = []
        for r in result_records:
            enriched_results.append({
                "testcase_id": r.testcase_id,
                "testcase_name": case_name_map.get(r.testcase_id, ""),
                "passed": r.passed,
                "actual_status": r.actual_status,
                "error_message": r.error_message,
            })
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
            send_webhook_notification(request.webhook_url, report_summary, enriched_results)
        )

    return response_data


@router.get("/reports", response_model=List[TestReportResponse], summary="报告列表")
def list_reports(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的测试报告列表"""
    reports = db.query(TestReport).filter(
        TestReport.owner_id == current_user.id
    ).order_by(TestReport.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for r in reports:
        pass_rate = (r.passed / r.total * 100) if r.total > 0 else 0
        result.append({
            "id": r.id,
            "name": r.name,
            "total": r.total,
            "passed": r.passed,
            "failed": r.failed,
            "duration_ms": r.duration_ms,
            "pass_rate": round(pass_rate, 2),
            "environment": r.environment,
            "created_at": r.created_at
        })
    return result


@router.get("/reports/{report_id}", response_model=TestReportDetail, summary="报告详情")
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定测试报告的详细信息"""
    report = db.query(TestReport).filter(
        TestReport.id == report_id,
        TestReport.owner_id == current_user.id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    results = db.query(TestResult).filter(TestResult.report_id == report_id).all()
    pass_rate = (report.passed / report.total * 100) if report.total > 0 else 0

    return {
        "id": report.id,
        "name": report.name,
        "total": report.total,
        "passed": report.passed,
        "failed": report.failed,
        "duration_ms": report.duration_ms,
        "pass_rate": round(pass_rate, 2),
        "environment": report.environment,
        "created_at": report.created_at,
        "results": results
    }


@router.get("/stats/summary", summary="统计数据")
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取平台统计数据"""
    total_cases = db.query(TestCase).filter(TestCase.owner_id == current_user.id).count()
    total_reports = db.query(TestReport).filter(TestReport.owner_id == current_user.id).count()

    # 最近10次报告的平均通过率
    recent_reports = db.query(TestReport).filter(
        TestReport.owner_id == current_user.id
    ).order_by(TestReport.created_at.desc()).limit(10).all()

    avg_pass_rate = 0
    if recent_reports:
        avg_pass_rate = sum(
            (r.passed / r.total * 100) if r.total > 0 else 0
            for r in recent_reports
        ) / len(recent_reports)

    # 今日执行次数
    from datetime import datetime, date
    today = date.today()
    today_executions = db.query(TestReport).filter(
        TestReport.owner_id == current_user.id,
        TestReport.created_at >= datetime.combine(today, datetime.min.time())
    ).count()

    return {
        "total_cases": total_cases,
        "total_reports": total_reports,
        "avg_pass_rate": round(avg_pass_rate, 2),
        "today_executions": today_executions
    }


@router.post("/webhook/test", summary="测试 Webhook 通知")
async def test_webhook(
    webhook_url: str,
    current_user: User = Depends(get_current_user)
):
    """发送一条测试消息到指定的 Webhook 地址，用于验证配置是否正确"""
    from pydantic import BaseModel

    mock_report = {
        "name": "Webhook 连通性测试",
        "total": 3,
        "passed": 2,
        "failed": 1,
        "pass_rate": 66.67,
        "duration_ms": 1234.56,
        "environment": "测试环境",
    }
    mock_results = [
        {"testcase_id": 1, "testcase_name": "登录接口测试", "passed": True, "actual_status": 200, "error_message": None},
        {"testcase_id": 2, "testcase_name": "获取用户信息", "passed": True, "actual_status": 200, "error_message": None},
        {"testcase_id": 3, "testcase_name": "提交订单接口", "passed": False, "actual_status": 500, "error_message": "状态码 500，预期 200"},
    ]
    result = await send_webhook_notification(webhook_url, mock_report, mock_results)
    return result

