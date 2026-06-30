from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Environment, User
from ..schemas import EnvironmentCreate, EnvironmentUpdate, EnvironmentResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/environments", tags=["环境管理"])


@router.post("/", response_model=EnvironmentResponse, summary="创建环境")
def create_environment(
    env: EnvironmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建测试环境配置"""
    # 检查名称是否已存在
    existing = db.query(Environment).filter(
        Environment.owner_id == current_user.id,
        Environment.name == env.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="环境名称已存在")

    db_env = Environment(
        name=env.name,
        base_url=env.base_url,
        variables=env.variables or "{}",
        owner_id=current_user.id
    )
    db.add(db_env)
    db.commit()
    db.refresh(db_env)
    return db_env


@router.get("/", response_model=List[EnvironmentResponse], summary="环境列表")
def list_environments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的所有环境"""
    return db.query(Environment).filter(Environment.owner_id == current_user.id).all()


@router.get("/{env_id}", response_model=EnvironmentResponse, summary="环境详情")
def get_environment(
    env_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个环境详情"""
    env = db.query(Environment).filter(
        Environment.id == env_id,
        Environment.owner_id == current_user.id
    ).first()
    if not env:
        raise HTTPException(status_code=404, detail="环境不存在")
    return env


@router.put("/{env_id}", response_model=EnvironmentResponse, summary="更新环境")
def update_environment(
    env_id: int,
    env: EnvironmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新环境配置"""
    db_env = db.query(Environment).filter(
        Environment.id == env_id,
        Environment.owner_id == current_user.id
    ).first()
    if not db_env:
        raise HTTPException(status_code=404, detail="环境不存在")

    update_data = env.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_env, key, value)

    db.commit()
    db.refresh(db_env)
    return db_env


@router.delete("/{env_id}", summary="删除环境")
def delete_environment(
    env_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除环境"""
    db_env = db.query(Environment).filter(
        Environment.id == env_id,
        Environment.owner_id == current_user.id
    ).first()
    if not db_env:
        raise HTTPException(status_code=404, detail="环境不存在")

    db.delete(db_env)
    db.commit()
    return {"message": "删除成功"}
