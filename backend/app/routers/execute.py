from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import TestCase, TestResult, TestReport, User
from ..schemas import ExecuteRequest, TestReportResponse, TestReportDetail, TestResultResponse
from ..auth import get_current_user
from ..executor import execute_single_testcase

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
    - 返回完整的测试报告（包含每条用例的执行结果）
    """
    # DEBUG
    print(f"[DEBUG] current_user.id = {current_user.id}")
    print(f"[DEBUG] request.testcase_ids = {request.testcase_ids}")

    # 获取要执行的用例
    query = db.query(TestCase).filter(TestCase.owner_id == current_user.id)
    if request.testcase_ids:
        query = query.filter(TestCase.id.in_(request.testcase_ids))
    testcases = query.all()

    print(f"[DEBUG] found testcases count = {len(testcases)}")

    if not testcases:
        raise HTTPException(status_code=404, detail=f"没有找到可执行的用例 (user_id={current_user.id})")

    # 创建报告
    report = TestReport(
        name=request.name or f"测试报告 #{db.query(TestReport).count() + 1}",
        total=len(testcases),
        owner_id=current_user.id
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # 逐条执行
    passed_count = 0
    failed_count = 0
    total_duration = 0
    results = []

    for testcase in testcases:
        result_data = await execute_single_testcase(testcase)

        test_result = TestResult(
            testcase_id=testcase.id,
            report_id=report.id,
            passed=result_data["passed"],
            actual_status=result_data["actual_status"],
            expected_status=testcase.expected_status,
            response_body=result_data["response_body"],
            duration_ms=result_data["duration_ms"],
            error_message=result_data["error_message"]
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
    return {
        "id": report.id,
        "name": report.name,
        "total": report.total,
        "passed": report.passed,
        "failed": report.failed,
        "duration_ms": report.duration_ms,
        "pass_rate": round(pass_rate, 2),
        "created_at": report.created_at,
        "results": result_records
    }


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
        "created_at": report.created_at,
        "results": results
    }
