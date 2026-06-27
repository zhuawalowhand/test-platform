from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import TestCase, User
from ..schemas import TestCaseCreate, TestCaseUpdate, TestCaseResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/testcases", tags=["用例管理"])


@router.post("/", response_model=TestCaseResponse, summary="创建用例")
def create_testcase(
    testcase: TestCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新的测试用例
    - method: GET / POST / PUT / DELETE
    - headers 和 body 使用 JSON 字符串格式
    """
    db_testcase = TestCase(**testcase.model_dump(), owner_id=current_user.id)
    db.add(db_testcase)
    db.commit()
    db.refresh(db_testcase)
    return db_testcase


@router.get("/", response_model=List[TestCaseResponse], summary="用例列表")
def list_testcases(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的所有测试用例（支持分页）"""
    return db.query(TestCase).filter(TestCase.owner_id == current_user.id).offset(skip).limit(limit).all()


@router.get("/{testcase_id}", response_model=TestCaseResponse, summary="获取用例详情")
def get_testcase(
    testcase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据 ID 获取单个测试用例"""
    testcase = db.query(TestCase).filter(
        TestCase.id == testcase_id,
        TestCase.owner_id == current_user.id
    ).first()
    if not testcase:
        raise HTTPException(status_code=404, detail="用例不存在")
    return testcase


@router.put("/{testcase_id}", response_model=TestCaseResponse, summary="更新用例")
def update_testcase(
    testcase_id: int,
    testcase: TestCaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新测试用例（只传需要修改的字段）"""
    db_testcase = db.query(TestCase).filter(
        TestCase.id == testcase_id,
        TestCase.owner_id == current_user.id
    ).first()
    if not db_testcase:
        raise HTTPException(status_code=404, detail="用例不存在")

    update_data = testcase.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_testcase, key, value)

    db.commit()
    db.refresh(db_testcase)
    return db_testcase


@router.delete("/{testcase_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除用例")
def delete_testcase(
    testcase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除测试用例"""
    db_testcase = db.query(TestCase).filter(
        TestCase.id == testcase_id,
        TestCase.owner_id == current_user.id
    ).first()
    if not db_testcase:
        raise HTTPException(status_code=404, detail="用例不存在")

    db.delete(db_testcase)
    db.commit()
