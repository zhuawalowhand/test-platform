from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import get_db, engine, Base
from .config import settings
from .models import User, TestCase, TestResult, TestReport, Environment, ScheduledTask  # noqa: F401
from .routers import users, testcases, execute, environments, schedules
from .scheduler import scheduler, load_all_jobs

# 启动时创建所有表
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：加载所有启用的定时任务
    scheduler.start()
    load_all_jobs()
    yield
    # 关闭：停止调度器
    scheduler.shutdown(wait=False)


app = FastAPI(
    title=settings.APP_NAME,
    description="接口测试平台 API - 支持用例管理、执行、报告、环境配置和定时任务",
    version="0.3.0",
    lifespan=lifespan
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


@app.get("/api/scheduler/status", tags=["调度器"])
def scheduler_status():
    """查看调度器状态和已注册的任务"""
    from .scheduler import get_jobs_info
    return {
        "running": scheduler.running,
        "job_count": len(scheduler.get_jobs()),
        "jobs": get_jobs_info()
    }
