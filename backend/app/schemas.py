from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


# ===== 用户相关 =====
class UserCreate(BaseModel):
    username: str = Field(..., description="用户名", examples=["testuser"])
    email: EmailStr = Field(..., description="邮箱地址", examples=["test@example.com"])
    password: str = Field(..., description="密码（至少6位）", examples=["123456"])


class UserResponse(BaseModel):
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str = Field(..., description="用户名", examples=["testuser"])
    password: str = Field(..., description="密码", examples=["123456"])


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, description="邮箱")
    password: Optional[str] = Field(None, description="新密码")


class Token(BaseModel):
    access_token: str = Field(..., description="JWT 访问令牌")
    token_type: str = Field(..., description="令牌类型", examples=["bearer"])


# ===== 用例相关 =====
class AssertionRule(BaseModel):
    type: str = Field(..., description="断言类型: body_contains, body_json, header, response_time")
    target: str = Field(..., description="断言目标")
    expected: Any = Field(..., description="预期值")


class TestCaseCreate(BaseModel):
    name: str = Field(..., description="用例名称", examples=["测试百度首页"])
    description: Optional[str] = Field(None, description="用例描述")
    method: str = Field(..., description="请求方法", examples=["GET"])
    url: str = Field(..., description="请求地址", examples=["https://www.baidu.com"])
    headers: Optional[str] = Field("{}", description="请求头（JSON字符串）")
    body: Optional[str] = Field("{}", description="请求体（JSON字符串）")
    expected_status: int = Field(200, description="预期状态码", examples=[200])
    tags: Optional[str] = Field(None, description="标签（逗号分隔）", examples=["smoke,regression"])
    assertions: Optional[str] = Field(None, description="高级断言规则（JSON）")
    sort_order: Optional[int] = Field(0, description="排序")


class TestCaseUpdate(BaseModel):
    name: Optional[str] = Field(None, description="用例名称")
    description: Optional[str] = Field(None, description="用例描述")
    method: Optional[str] = Field(None, description="请求方法")
    url: Optional[str] = Field(None, description="请求地址")
    headers: Optional[str] = Field(None, description="请求头（JSON字符串）")
    body: Optional[str] = Field(None, description="请求体（JSON字符串）")
    expected_status: Optional[int] = Field(None, description="预期状态码")
    tags: Optional[str] = Field(None, description="标签")
    assertions: Optional[str] = Field(None, description="高级断言规则")
    sort_order: Optional[int] = Field(None, description="排序")


class TestCaseResponse(BaseModel):
    id: int = Field(..., description="用例ID")
    name: str = Field(..., description="用例名称")
    description: Optional[str] = Field(None, description="用例描述")
    method: str = Field(..., description="请求方法")
    url: str = Field(..., description="请求地址")
    headers: Optional[str] = Field(None, description="请求头")
    body: Optional[str] = Field(None, description="请求体")
    expected_status: int = Field(..., description="预期状态码")
    tags: Optional[str] = Field(None, description="标签")
    assertions: Optional[str] = Field(None, description="断言规则")
    sort_order: int = Field(0, description="排序")
    owner_id: int = Field(..., description="所属用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


# ===== 执行与报告 =====
class ExecuteRequest(BaseModel):
    testcase_ids: Optional[List[int]] = Field(
        None,
        description="要执行的用例ID列表，留空或null则执行全部",
        examples=[None, [1, 2, 3]]
    )
    name: Optional[str] = Field(None, description="报告名称", examples=["回归测试 v1.0"])
    environment_id: Optional[int] = Field(None, description="环境ID")
    webhook_url: Optional[str] = Field(None, description="Webhook 通知地址（钉钉/飞书/企微/Slack）")


class TestResultResponse(BaseModel):
    id: int = Field(..., description="结果ID")
    testcase_id: int = Field(..., description="用例ID")
    passed: bool = Field(..., description="是否通过")
    actual_status: Optional[int] = Field(None, description="实际状态码")
    expected_status: int = Field(..., description="预期状态码")
    response_body: Optional[str] = Field(None, description="响应内容")
    duration_ms: Optional[float] = Field(None, description="耗时（毫秒）")
    error_message: Optional[str] = Field(None, description="错误信息")
    assertion_results: Optional[str] = Field(None, description="断言结果详情")
    executed_at: datetime = Field(..., description="执行时间")

    class Config:
        from_attributes = True


class TestReportResponse(BaseModel):
    id: int = Field(..., description="报告ID")
    name: Optional[str] = Field(None, description="报告名称")
    total: int = Field(..., description="总用例数")
    passed: int = Field(..., description="通过数")
    failed: int = Field(..., description="失败数")
    duration_ms: float = Field(..., description="总耗时（毫秒）")
    pass_rate: float = Field(..., description="通过率（%）")
    environment: Optional[str] = Field(None, description="执行环境")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class TestReportDetail(TestReportResponse):
    results: List[TestResultResponse] = Field(..., description="执行结果详情")


# ===== 环境配置 =====
class EnvironmentCreate(BaseModel):
    name: str = Field(..., description="环境名称", examples=["dev"])
    base_url: str = Field(..., description="基础URL", examples=["https://dev.api.example.com"])
    variables: Optional[str] = Field("{}", description="环境变量（JSON）")


class EnvironmentUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    variables: Optional[str] = None


class EnvironmentResponse(BaseModel):
    id: int
    name: str
    base_url: str
    variables: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ===== 定时任务 =====
class ScheduledTaskCreate(BaseModel):
    name: str = Field(..., description="任务名称")
    cron_expression: str = Field(..., description="Cron 表达式", examples=["0 0 * * *"])
    testcase_ids: Optional[str] = Field("[]", description="用例ID列表（JSON）")
    environment_id: Optional[int] = Field(None, description="环境ID")
    webhook_url: Optional[str] = Field(None, description="通知 Webhook URL")


class ScheduledTaskUpdate(BaseModel):
    name: Optional[str] = None
    cron_expression: Optional[str] = None
    testcase_ids: Optional[str] = None
    environment_id: Optional[int] = None
    enabled: Optional[bool] = None
    webhook_url: Optional[str] = None


class ScheduledTaskResponse(BaseModel):
    id: int
    name: str
    cron_expression: str
    testcase_ids: Optional[str]
    environment_id: Optional[int]
    enabled: bool
    last_run: Optional[datetime]
    webhook_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
