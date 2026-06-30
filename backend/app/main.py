from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import get_db, engine, Base
from .config import settings
from .models import User, TestCase, TestResult, TestReport, Environment, ScheduledTask  # noqa: F401
from .routers import users, testcases, execute, environments, schedules

# 启动时创建所有表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="接口测试平台 API - 支持用例管理、执行、报告、环境配置和定时任务",
    version="0.2.0"
)

# 注册路由
app.include_router(users.router)
app.include_router(testcases.router)
app.include_router(execute.router)
app.include_router(environments.router)
app.include_router(schedules.router)


@app.get("/")
def root():
    return {"message": "Test Platform API is running"}


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """检查数据库连接"""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}
