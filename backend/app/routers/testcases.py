from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import TestCase, User
from ..schemas import TestCaseCreate, TestCaseUpdate, TestCaseResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/testcases", tags=["testcases"])


@router.post("/", response_model=TestCaseResponse)
def create_testcase(
    testcase: TestCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建测试用例"""
    db_testcase = TestCase(**testcase.model_dump(), owner_id=current_user.id)
    db.add(db_testcase)
    db.commit()
    db.refresh(db_testcase)
    return db_testcase


@router.get("/", response_model=List[TestCaseResponse])
def list_testcases(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的测试用例列表"""
    return db.query(TestCase).filter(TestCase.owner_id == current_user.id).offset(skip).limit(limit).all()


@router.get("/{testcase_id}", response_model=TestCaseResponse)
def get_testcase(
    testcase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个测试用例"""
    testcase = db.query(TestCase).filter(
        TestCase.id == testcase_id,
        TestCase.owner_id == current_user.id
    ).first()
    if not testcase:
        raise HTTPException(status_code=404, detail="TestCase not found")
    return testcase


@router.put("/{testcase_id}", response_model=TestCaseResponse)
def update_testcase(
    testcase_id: int,
    testcase: TestCaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新测试用例"""
    db_testcase = db.query(TestCase).filter(
        TestCase.id == testcase_id,
        TestCase.owner_id == current_user.id
    ).first()
    if not db_testcase:
        raise HTTPException(status_code=404, detail="TestCase not found")

    update_data = testcase.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_testcase, key, value)

    db.commit()
    db.refresh(db_testcase)
    return db_testcase


@router.delete("/{testcase_id}", status_code=status.HTTP_204_NO_CONTENT)
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
        raise HTTPException(status_code=404, detail="TestCase not found")

    db.delete(db_testcase)
    db.commit()
