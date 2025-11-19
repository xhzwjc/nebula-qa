# utils/request_util.py
import requests
import allure
import re
from utils.yaml_util import read_extract, write_extract
from utils.log import logger

class RequestUtil:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = ""

    def replace_vars(self, obj):
        """递归替换 ${var}"""
        if obj is None:
            return obj
        if isinstance(obj, dict):
            return {k: self.replace_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.replace_vars(i) for i in obj]
        elif isinstance(obj, str):
            pattern = r"\$\{(\w+)\}"
            while re.search(pattern, obj):
                m = re.search(pattern, obj)
                key = m.group(1)
                value = read_extract(key)
                if value is None:
                    raise ValueError(f"依赖变量未找到: ${{{key}}}")
                obj = obj.replace(m.group(0), str(value))
            return obj
        return obj

    def standard_url(self, case):
        url = case["url"]
        if case.get("path_params"):
            for k, v in case["path_params"].items():
                v = self.replace_vars(v)
                url = url.replace(f"{{{k}}}", str(v))
        return self.base_url + url

    def extract_value(self, res, expr):
        """完美兼容你登录返回的提取方式"""
        if not expr.startswith("content."):
            return None

        path = expr.replace("content.", "").split(".")
        try:
            data = res.json()
        except Exception as e:
            logger.error(f"响应非JSON: {res.text}")
            raise

        current = data
        for key in path:
            if not isinstance(current, dict):
                raise TypeError(f"路径错误: 在 {key} 前已不是dict，而是 {type(current)}")
            if key not in current:
                raise KeyError(f"键不存在: {key}")
            current = current[key]   # 这里用 [] 是安全的，因为上面已判断是 dict

        return current

    def assert_result(self, case, res):
        if "validate" not in case:
            return
        for item in case["validate"]:
            for method, expect in item.items():
                if method == "equals":
                    for field, val in expect.items():
                        actual = self.extract_value(res, f"content.{field}")
                        assert actual == val, f"断言失败 → 字段: {field} | 期望: {val} | 实际: {actual}"

    @allure.step("执行用例: {case[name]}")
    def send_request(self, case):
        logger.info(f"【{case['name']}】开始执行")

        method = case["method"].upper()
        url = self.standard_url(case)

        headers = self.replace_vars(case.get("headers", {}))
        params = self.replace_vars(case.get("params"))
        data = self.replace_vars(case.get("data"))
        json_data = self.replace_vars(case.get("json"))

        res = self.session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            data=data,
            json=json_data,
            timeout=30,
            verify=False
        )

        logger.info(f"响应状态码: {res.status_code}")
        logger.info(f"响应内容: {res.text[:1000]}")

        # 提取
        if "extract" in case:
            for var_name, expr in case["extract"].items():
                value = self.extract_value(res, expr)
                write_extract({var_name: value})
                logger.info(f"提取成功 → {var_name} = {value}")

        # 断言
        self.assert_result(case, res)