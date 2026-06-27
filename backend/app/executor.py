import json
import time
import httpx
from typing import Optional

from .models import TestCase, TestResult, TestReport


async def execute_single_testcase(testcase: TestCase) -> dict:
    """
    执行单个测试用例
    返回: {passed, actual_status, response_body, duration_ms, error_message}
    """
    start_time = time.time()

    try:
        # 解析 headers 和 body
        headers = json.loads(testcase.headers) if testcase.headers else {}
        body = json.loads(testcase.body) if testcase.body else None

        # 发送请求
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            if testcase.method.upper() in ["POST", "PUT", "PATCH"]:
                response = await client.request(
                    method=testcase.method.upper(),
                    url=testcase.url,
                    headers=headers,
                    json=body
                )
            else:
                response = await client.request(
                    method=testcase.method.upper(),
                    url=testcase.url,
                    headers=headers
                )

        duration_ms = (time.time() - start_time) * 1000

        # 判断是否通过
        actual_status = response.status_code
        passed = actual_status == testcase.expected_status

        # 截取响应内容（防止太长）
        response_text = response.text[:2000] if response.text else ""

        return {
            "passed": passed,
            "actual_status": actual_status,
            "response_body": response_text,
            "duration_ms": round(duration_ms, 2),
            "error_message": None
        }

    except httpx.TimeoutException:
        duration_ms = (time.time() - start_time) * 1000
        return {
            "passed": False,
            "actual_status": None,
            "response_body": None,
            "duration_ms": round(duration_ms, 2),
            "error_message": "请求超时（30秒）"
        }
    except httpx.ConnectError as e:
        duration_ms = (time.time() - start_time) * 1000
        return {
            "passed": False,
            "actual_status": None,
            "response_body": None,
            "duration_ms": round(duration_ms, 2),
            "error_message": f"连接失败: {str(e)}"
        }
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        return {
            "passed": False,
            "actual_status": None,
            "response_body": None,
            "duration_ms": round(duration_ms, 2),
            "error_message": f"执行异常: {str(e)}"
        }
