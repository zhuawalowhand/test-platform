import httpx
import logging
import hashlib
import hmac
import base64
import time
import urllib.parse
from typing import Optional

logger = logging.getLogger(__name__)


def _detect_platform(url: str) -> str:
    """根据 webhook URL 自动识别平台"""
    if "dingtalk" in url or "oapi.dingtalk.com" in url:
        return "dingtalk"
    elif "feishu" in url or "larksuite" in url:
        return "feishu"
    elif "qyapi.weixin" in url or "wechat" in url:
        return "wecom"
    elif "slack" in url or "hooks.slack.com" in url:
        return "slack"
    return "generic"


def _dingtalk_sign(secret: str) -> tuple:
    """钉钉加签（如果 URL 含 secret 参数）"""
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        secret.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign


def _build_dingtalk_body(report: dict, results: list) -> dict:
    """钉钉 Markdown 消息"""
    emoji = "✅" if report["pass_rate"] == 100 else "⚠️" if report["pass_rate"] >= 80 else "❌"
    failed_list = ""
    for r in results:
        if not r.get("passed"):
            name = r.get("testcase_name") or f"用例#{r['testcase_id']}"
            error = r.get("error_message") or f"状态码 {r.get('actual_status', '?')}"
            failed_list += f"\n> - {name}：{error}"

    text = (
        f"## {emoji} 测试报告：{report['name']}\n\n"
        f"- **总数**: {report['total']}  "
        f"- **通过**: {report['passed']} ✅  "
        f"- **失败**: {report['failed']} ❌\n"
        f"- **通过率**: {report['pass_rate']}%\n"
        f"- **耗时**: {report['duration_ms']}ms\n"
        f"- **环境**: {report.get('environment') or '默认'}\n"
    )
    if failed_list:
        text += f"\n### 失败用例{failed_list}"

    return {
        "msgtype": "markdown",
        "markdown": {"title": f"{emoji} 测试报告 {report['pass_rate']}%", "text": text},
    }


def _build_feishu_body(report: dict, results: list) -> dict:
    """飞书富文本消息"""
    emoji = "✅" if report["pass_rate"] == 100 else "⚠️" if report["pass_rate"] >= 80 else "❌"
    failed_items = []
    for r in results:
        if not r.get("passed"):
            name = r.get("testcase_name") or f"用例#{r['testcase_id']}"
            error = r.get("error_message") or f"状态码 {r.get('actual_status', '?')}"
            failed_items.append([{"tag": "text", "text": f"❌ {name}：{error}"}])

    content = [
        [
            {"tag": "text", "text": f"总数: {report['total']}  "},
            {"tag": "text", "text": f"通过: {report['passed']} ✅  "},
            {"tag": "text", "text": f"失败: {report['failed']} ❌"},
        ],
        [
            {"tag": "text", "text": f"通过率: {report['pass_rate']}%  |  耗时: {report['duration_ms']}ms"},
        ],
        [
            {"tag": "text", "text": f"环境: {report.get('environment') or '默认'}"},
        ],
    ]
    if failed_items:
        content.append([{"tag": "text", "text": "\n失败用例:"}])
        content.extend(failed_items)

    return {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": f"{emoji} 测试报告：{report['name']}",
                    "content": content,
                }
            }
        },
    }


def _build_wecom_body(report: dict, results: list) -> dict:
    """企业微信 Markdown 消息"""
    emoji = "✅" if report["pass_rate"] == 100 else "⚠️" if report["pass_rate"] >= 80 else "❌"
    failed_list = ""
    for r in results:
        if not r.get("passed"):
            name = r.get("testcase_name") or f"用例#{r['testcase_id']}"
            error = r.get("error_message") or f"状态码 {r.get('actual_status', '?')}"
            failed_list += f"\n> - {name}：{error}"

    content = (
        f"## {emoji} 测试报告：{report['name']}\n"
        f"> 总数: <font color=\"info\">{report['total']}</font>  "
        f"通过: <font color=\"info\">{report['passed']}</font>  "
        f"失败: <font color=\"warning\">{report['failed']}</font>\n"
        f"> 通过率: <font color=\"{'info' if report['pass_rate'] >= 80 else 'warning'}\">{report['pass_rate']}%</font>\n"
        f"> 耗时: {report['duration_ms']}ms | 环境: {report.get('environment') or '默认'}\n"
    )
    if failed_list:
        content += f"\n**失败用例:**{failed_list}"

    return {"msgtype": "markdown", "markdown": {"content": content}}


def _build_slack_body(report: dict, results: list) -> dict:
    """Slack Block Kit 消息"""
    emoji = ":white_check_mark:" if report["pass_rate"] == 100 else ":warning:" if report["pass_rate"] >= 80 else ":x:"
    failed_text = ""
    for r in results:
        if not r.get("passed"):
            name = r.get("testcase_name") or f"用例#{r['testcase_id']}"
            error = r.get("error_message") or f"状态码 {r.get('actual_status', '?')}"
            failed_text += f"• {name}：{error}\n"

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"{emoji} 测试报告：{report['name']}"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*总数:* {report['total']}"},
                {"type": "mrkdwn", "text": f"*通过:* {report['passed']} ✅"},
                {"type": "mrkdwn", "text": f"*失败:* {report['failed']} ❌"},
                {"type": "mrkdwn", "text": f"*通过率:* {report['pass_rate']}%"},
                {"type": "mrkdwn", "text": f"*耗时:* {report['duration_ms']}ms"},
                {"type": "mrkdwn", "text": f"*环境:* {report.get('environment') or '默认'}"},
            ],
        },
    ]
    if failed_text:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*失败用例:*\n{failed_text}"}})

    return {"blocks": blocks}


def _build_generic_body(report: dict, results: list) -> dict:
    """通用 JSON 格式"""
    return {
        "event": "test_report",
        "data": {
            "name": report["name"],
            "total": report["total"],
            "passed": report["passed"],
            "failed": report["failed"],
            "pass_rate": report["pass_rate"],
            "duration_ms": report["duration_ms"],
            "environment": report.get("environment"),
            "results": [
                {
                    "testcase_id": r["testcase_id"],
                    "testcase_name": r.get("testcase_name"),
                    "passed": r.get("passed"),
                    "actual_status": r.get("actual_status"),
                    "error_message": r.get("error_message"),
                }
                for r in results
            ],
        },
    }


async def send_webhook_notification(
    webhook_url: str,
    report: dict,
    results: list,
    platform: Optional[str] = None,
) -> dict:
    """
    发送 Webhook 通知
    :param webhook_url: Webhook 地址
    :param report: 报告摘要 dict
    :param results: 执行结果列表
    :param platform: 平台名 (dingtalk/feishu/wecom/slack/generic)，None 则自动识别
    :return: {"success": bool, "message": str}
    """
    if not webhook_url:
        return {"success": False, "message": "未配置 Webhook URL"}

    if not platform:
        platform = _detect_platform(webhook_url)

    builders = {
        "dingtalk": _build_dingtalk_body,
        "feishu": _build_feishu_body,
        "wecom": _build_wecom_body,
        "slack": _build_slack_body,
        "generic": _build_generic_body,
    }
    builder = builders.get(platform, _build_generic_body)
    body = builder(report, results)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook_url, json=body)
            if resp.status_code in (200, 204):
                logger.info(f"Webhook 通知发送成功 [{platform}]: {webhook_url[:60]}...")
                return {"success": True, "message": f"通知发送成功（{platform}）"}
            else:
                logger.warning(f"Webhook 返回非200: {resp.status_code} {resp.text[:200]}")
                return {"success": False, "message": f"Webhook 返回状态码 {resp.status_code}"}
    except httpx.TimeoutException:
        logger.error(f"Webhook 超时: {webhook_url[:60]}...")
        return {"success": False, "message": "Webhook 请求超时"}
    except Exception as e:
        logger.error(f"Webhook 发送失败: {e}")
        return {"success": False, "message": f"发送失败: {str(e)}"}
