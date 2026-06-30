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
    tags = Column(String(500))  # 逗号分隔的标签
    assertions = Column(Text)  # JSON: 高级断言规则
    sort_order = Column(Integer, default=0)  # 排序字段
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
    assertion_results = Column(Text)  # JSON: 断言结果详情
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
    environment = Column(String(50))  # 执行环境
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Environment(Base):
    """测试环境配置"""
    __tablename__ = "environments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True)  # dev, staging, prod
    base_url = Column(String(500))  # 基础 URL
    variables = Column(Text)  # JSON: 环境变量
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ScheduledTask(Base):
    """定时任务"""
    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200))
    cron_expression = Column(String(100))  # cron 表达式
    testcase_ids = Column(Text)  # JSON: 要执行的用例ID列表
    environment_id = Column(Integer, ForeignKey("environments.id"))
    enabled = Column(Boolean, default=True)
    last_run = Column(DateTime(timezone=True))
    webhook_url = Column(String(500))  # 通知 webhook
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
