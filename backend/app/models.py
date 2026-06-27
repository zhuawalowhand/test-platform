from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(128))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TestCase(Base):
    __tablename__ = "testcases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), index=True)
    description = Column(Text)
    method = Column(String(10))  # GET, POST, PUT, DELETE
    url = Column(String(500))
    headers = Column(Text)  # JSON string
    body = Column(Text)  # JSON string
    expected_status = Column(Integer, default=200)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TestResult(Base):
    """单条用例的执行结果"""
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    testcase_id = Column(Integer, ForeignKey("testcases.id"))
    report_id = Column(Integer, ForeignKey("test_reports.id"))
    passed = Column(Boolean)  # 是否通过
    actual_status = Column(Integer)  # 实际状态码
    expected_status = Column(Integer)  # 预期状态码
    response_body = Column(Text)  # 响应内容
    duration_ms = Column(Float)  # 耗时（毫秒）
    error_message = Column(Text)  # 错误信息（如果有）
    executed_at = Column(DateTime(timezone=True), server_default=func.now())


class TestReport(Base):
    """测试报告（一次执行一批用例）"""
    __tablename__ = "test_reports"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200))
    total = Column(Integer, default=0)  # 总用例数
    passed = Column(Integer, default=0)  # 通过数
    failed = Column(Integer, default=0)  # 失败数
    duration_ms = Column(Float, default=0)  # 总耗时
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
