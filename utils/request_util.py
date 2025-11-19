"""Request utilities with optional mock responses and no third-party deps."""
from __future__ import annotations

import json
import re
import ssl
from pathlib import Path
from typing import Any, Dict, Optional
from urllib import parse as urllib_parse
from urllib import request as urllib_request

import allure

from utils.yaml_util import read_extract, write_extract
from utils.log import logger

MOCK_RESPONSES_FILE = Path("data/mock_responses.yaml")
if MOCK_RESPONSES_FILE.exists():
    _mock_data = json.loads(MOCK_RESPONSES_FILE.read_text(encoding="utf-8"))
    MOCK_RESPONSES = {
        f"{item['method'].upper()} {item['url']}": item for item in _mock_data
    }
else:
    MOCK_RESPONSES = {}


class _SimpleResponse:
    def __init__(self, status_code: int, text: str, headers: Optional[Dict[str, str]] = None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}

    def json(self) -> Dict[str, Any]:
        return json.loads(self.text)


class _MockResponse(_SimpleResponse):
    def __init__(self, status_code: int, payload: Dict[str, Any]):
        super().__init__(status_code=status_code, text=json.dumps(payload, ensure_ascii=False))
        self._payload = payload

    def json(self) -> Dict[str, Any]:
        return self._payload


class RequestUtil:
    def __init__(self) -> None:
        self.base_url = ""
        self.timeout = 30

    def replace_vars(self, obj: Any):
        if obj is None:
            return obj
        if isinstance(obj, dict):
            return {k: self.replace_vars(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.replace_vars(i) for i in obj]
        if isinstance(obj, str):
            pattern = r"\$\{(\w+)\}"
            while True:
                match = re.search(pattern, obj)
                if not match:
                    break
                key = match.group(1)
                value = read_extract(key)
                if value is None:
                    raise ValueError(f"依赖变量未找到: ${{{key}}}")
                obj = obj.replace(match.group(0), str(value))
            return obj
        return obj

    def standard_url(self, case: Dict[str, Any]) -> str:
        url = case["url"]
        if case.get("path_params"):
            for k, v in case["path_params"].items():
                v = self.replace_vars(v)
                url = url.replace(f"{{{k}}}", str(v))
        return self.base_url.rstrip("/") + url

    def extract_value(self, res: _SimpleResponse, expr: str):
        if not expr.startswith("content."):
            return None
        path = expr.replace("content.", "").split(".")
        try:
            data = res.json()
        except Exception:
            logger.error("响应非JSON: %s", res.text)
            raise

        current: Any = data
        for key in path:
            if not isinstance(current, dict):
                raise TypeError(f"路径错误: 在 {key} 前已不是dict，而是 {type(current)}")
            if key not in current:
                raise KeyError(f"键不存在: {key}")
            current = current[key]
        return current

    def assert_result(self, case: Dict[str, Any], res: _SimpleResponse) -> None:
        if "validate" not in case:
            return
        for item in case["validate"]:
            for method, expect in item.items():
                if method == "equals":
                    for field, val in expect.items():
                        actual = self.extract_value(res, f"content.{field}")
                        assert actual == val, (
                            f"断言失败 → 字段: {field} | 期望: {val} | 实际: {actual}"
                        )

    def _build_request_data(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, Any]],
        params: Optional[Dict[str, Any]],
        data: Any,
        json_data: Any,
    ) -> tuple[str, Dict[str, str], Optional[bytes]]:
        if params:
            query = urllib_parse.urlencode(params, doseq=True)
            separator = "&" if urllib_parse.urlparse(url).query else "?"
            url = f"{url}{separator}{query}"
        headers = {k: str(v) for k, v in (headers or {}).items()}
        body: Optional[bytes] = None
        if json_data is not None:
            headers.setdefault("Content-Type", "application/json")
            body = json.dumps(json_data, ensure_ascii=False).encode("utf-8")
        elif data is not None:
            if isinstance(data, dict):
                headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
                body = urllib_parse.urlencode(data, doseq=True).encode("utf-8")
            elif isinstance(data, str):
                body = data.encode("utf-8")
            else:
                body = data
        return url, headers, body

    def _perform_http_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        body: Optional[bytes],
        timeout: float,
        verify: bool,
    ) -> _SimpleResponse:
        request = urllib_request.Request(url=url, data=body, headers=headers, method=method)
        context = None
        if url.lower().startswith("https") and not verify:
            context = ssl._create_unverified_context()
        with urllib_request.urlopen(request, timeout=timeout, context=context) as resp:
            payload = resp.read().decode("utf-8")
            status = resp.getcode()
            headers = dict(resp.headers.items())
        return _SimpleResponse(status_code=status, text=payload, headers=headers)

    def _try_mock(self, method: str, case_url: str) -> Optional[_MockResponse]:
        key = f"{method} {case_url}"
        if key not in MOCK_RESPONSES:
            return None
        mock = MOCK_RESPONSES[key]
        return _MockResponse(status_code=mock.get("status_code", 200), payload=mock["body"])

    @allure.step("执行用例: {case[name]}")
    def send_request(self, case: Dict[str, Any]) -> None:
        logger.info("【%s】开始执行", case["name"])

        method = case["method"].upper()
        url = self.standard_url(case)

        headers = self.replace_vars(case.get("headers", {}))
        params = self.replace_vars(case.get("params"))
        data = self.replace_vars(case.get("data"))
        json_data = self.replace_vars(case.get("json"))

        mock_response = self._try_mock(method, case["url"])
        if mock_response is not None:
            res = mock_response
        else:
            request_url, prepared_headers, body = self._build_request_data(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data,
                json_data=json_data,
            )
            timeout = case.get("timeout", self.timeout)
            res = self._perform_http_request(
                method=method,
                url=request_url,
                headers=prepared_headers,
                body=body,
                timeout=timeout,
                verify=case.get("verify", False),
            )

        logger.info("响应状态码: %s", res.status_code)
        logger.info("响应内容: %s", res.text[:1000])

        if "extract" in case:
            for var_name, expr in case["extract"].items():
                value = self.extract_value(res, expr)
                write_extract({var_name: value})
                logger.info("提取成功 → %s = %s", var_name, value)

        self.assert_result(case, res)
