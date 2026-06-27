from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserResponse, UserLogin, Token
from ..auth import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/users", tags=["用户管理"])


@router.post("/register", response_model=UserResponse, summary="用户注册")
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    注册新用户
    - 用户名不能重复
    - 邮箱不能重复
    - 密码会被加密存储
    """
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token, summary="用户登录")
def login(user: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录，返回 JWT token
    - token 有效期 24 小时
    - 后续请求需在 Header 中携带: Authorization: Bearer {token}
    """
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse, summary="获取当前用户")
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户的信息（需要认证）"""
    return current_user
