from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import ScheduledTask, User
from ..schemas import ScheduledTaskCreate, ScheduledTaskUpdate, ScheduledTaskResponse
from ..auth import get_current_user

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
