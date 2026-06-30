import json
import time
import re
import httpx
from typing import Optional, Dict, Any, List

from .models import TestCase, TestResult, TestReport, Environment


def replace_variables(text: str, variables: Dict[str, str]) -> str:
    """替换文本中的变量 {{variable_name}}"""
    if not text:
        return text
    for key, value in variables.items():
        text = text.replace(f"{{{{{key}}}}}", str(value))
    return text


def run_assertions(response: httpx.Response, duration_ms: float, assertions: List[Dict]) -> tuple:
    """
    执行高级断言
    返回: (all_passed, assertion_results)
    """
    results = []
    all_passed = True

    for assertion in assertions:
        assertion_type = assertion.get("type")
        target = assertion.get("target", "")
        expected = assertion.get("expected")
        passed = False
        actual = None
        message = ""

        try:
            if assertion_type == "body_contains":
                actual = response.text[:200]
                passed = str(expected) in response.text
                message = f"响应体{'包含' if passed else '不包含'} '{expected}'"

            elif assertion_type == "body_not_contains":
                actual = response.text[:200]
                passed = str(expected) not in response.text
                message = f"响应体{'不包含' if passed else '包含'} '{expected}'"

            elif assertion_type == "body_json":
                try:
                    json_body = response.json()
                    keys = target.split(".")
                    value = json_body
                    for key in keys:
                        if key.isdigit():
                            value = value[int(key)]
                        else:
                            value = value[key]
                    actual = str(value)
                    passed = str(value) == str(expected)
                    message = f"JSON {target} = {value}, 预期 {expected}"
                except (KeyError, IndexError, TypeError) as e:
                    message = f"JSON 路径 {target} 不存在"
                    passed = False

            elif assertion_type == "header":
                actual = response.headers.get(target, "")
                passed = actual == str(expected)
                message = f"Header {target} = {actual}, 预期 {expected}"

            elif assertion_type == "header_contains":
                actual = response.headers.get(target, "")
                passed = str(expected) in actual
                message = f"Header {target} {'包含' if passed else '不包含'} '{expected}'"

            elif assertion_type == "response_time":
                actual = round(duration_ms, 2)
                operator = assertion.get("operator", "<")
                if operator == "<":
                    passed = duration_ms < expected
                elif operator == "<=":
                    passed = duration_ms <= expected
                elif operator == ">":
                    passed = duration_ms > expected
                elif operator == ">=":
                    passed = duration_ms >= expected
                message = f"响应时间 {actual}ms {operator} {expected}ms"

            elif assertion_type == "body_regex":
                match = re.search(target, response.text)
                passed = match is not None
                actual = match.group(0) if match else None
                message = f"正则 {target} {'匹配' if passed else '未匹配'}"

        except Exception as e:
            passed = False
            message = f"断言执行异常: {str(e)}"

        if not passed:
            all_passed = False

        results.append({
            "type": assertion_type,
            "target": target,
            "expected": expected,
            "actual": actual,
            "passed": passed,
            "message": message
        })

    return all_passed, results


async def execute_single_testcase(
    testcase: TestCase,
    environment: Optional[Environment] = None
) -> dict:
    """
    执行单个测试用例
    返回: {passed, actual_status, response_body, duration_ms, error_message, assertion_results}
    """
    start_time = time.time()

    # 准备环境变量
    env_vars = {}
    base_url = ""
    if environment:
        base_url = environment.base_url or ""
        if environment.variables:
            try:
                env_vars = json.loads(environment.variables)
            except:
                env_vars = {}

    try:
        # 解析并替换变量
        url = testcase.url
        if base_url and not url.startswith("http"):
            url = base_url.rstrip("/") + "/" + url.lstrip("/")
        url = replace_variables(url, env_vars)

        headers = {}
        if testcase.headers:
            try:
                headers = json.loads(replace_variables(testcase.headers, env_vars))
            except:
                headers = {}

        body = None
        if testcase.body:
            try:
                body_text = replace_variables(testcase.body, env_vars)
                body = json.loads(body_text)
            except:
                body = None

        # 发送请求
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            if testcase.method.upper() in ["POST", "PUT", "PATCH"]:
                response = await client.request(
                    method=testcase.method.upper(),
                    url=url,
                    headers=headers,
                    json=body
                )
            else:
                response = await client.request(
                    method=testcase.method.upper(),
                    url=url,
                    headers=headers
                )

        duration_ms = (time.time() - start_time) * 1000

        # 基础状态码判断
        actual_status = response.status_code
        status_passed = actual_status == testcase.expected_status

        # 高级断言
        assertion_results = []
        assertions_passed = True
        if testcase.assertions:
            try:
                assertions = json.loads(testcase.assertions)
                if assertions:
                    assertions_passed, assertion_results = run_assertions(
                        response, duration_ms, assertions
                    )
            except:
                pass

        passed = status_passed and assertions_passed

        # 截取响应内容
        response_text = response.text[:2000] if response.text else ""

        return {
            "passed": passed,
            "actual_status": actual_status,
            "response_body": response_text,
            "duration_ms": round(duration_ms, 2),
            "error_message": None,
            "assertion_results": json.dumps(assertion_results, ensure_ascii=False) if assertion_results else None
        }

    except httpx.TimeoutException:
        duration_ms = (time.time() - start_time) * 1000
        return {
            "passed": False,
            "actual_status": None,
            "response_body": None,
            "duration_ms": round(duration_ms, 2),
            "error_message": "请求超时（30秒）",
            "assertion_results": None
        }
    except httpx.ConnectError as e:
        duration_ms = (time.time() - start_time) * 1000
        return {
            "passed": False,
            "actual_status": None,
            "response_body": None,
            "duration_ms": round(duration_ms, 2),
            "error_message": f"连接失败: {str(e)}",
            "assertion_results": None
        }
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        return {
            "passed": False,
            "actual_status": None,
            "response_body": None,
            "duration_ms": round(duration_ms, 2),
            "error_message": f"执行异常: {str(e)}",
            "assertion_results": None
        }
