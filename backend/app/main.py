from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import get_db, engine, Base
from .config import settings

# 启动时创建所有表
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)


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
