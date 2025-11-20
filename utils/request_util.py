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

    # utils/request_util.py (修改replace_vars方法)
    def replace_vars(self, obj, case_name=""):
        """递归替换 ${var}，修复类型错误"""
        if obj is None:
            return obj
        if isinstance(obj, dict):
            # 对字典的每个值进行替换，确保返回的仍是字典
            new_dict = {}
            for k, v in obj.items():
                new_dict[k] = self.replace_vars(v, case_name)
            return new_dict
        elif isinstance(obj, list):
            # 对列表的每个元素进行替换，确保返回的仍是列表
            return [self.replace_vars(item, case_name) for item in obj]
        elif isinstance(obj, str):
            pattern = r"\$\{(\w+)\}"
            # 只替换字符串中的变量，不改变其他类型
            if re.search(pattern, obj):
                m = re.search(pattern, obj)
                key = m.group(1)
                
                # 从extract文件中读取
                value = read_extract(key)
                
                if value is None:
                    # 第一个用例（登录）还没执行时，token 不存在，这里先不报错
                    if key == "token" and "01-用户登录" in case_name:
                        return obj  # 登录用例本身不需要 token
                    raise ValueError(f"依赖变量未找到: ${{{key}}}")
                return obj.replace(m.group(0), str(value))
            return obj
        return obj  # 非字符串/字典/列表类型直接返回
    def standard_url(self, case):
        url = case["url"]
        if case.get("path_params"):
            for k, v in case["path_params"].items():
                v = self.replace_vars(v, case.get("name", ""))
                url = url.replace(f"{{{k}}}", str(v))
        return self.base_url + url

    def extract_value(self, res, expr):
        """完美兼容你登录返回的提取方式"""
        logger.info(f"提取表达式: {expr}")
        if not expr.startswith("content."):
            return None

        path = expr.replace("content.", "").split(".")
        try:
            data = res.json()
            logger.info(f"响应数据结构: {type(data)}, 键: {list(data.keys()) if isinstance(data, dict) else '非字典'}")
        except Exception as e:
            logger.error(f"响应非JSON: {res.text}")
            raise

        current = data
        for key in path:
            if not isinstance(current, dict):
                raise TypeError(f"路径错误: 在 {key} 前已不是dict，而是 {type(current)}")
            if key not in current:
                raise KeyError(f"键不存在: {key}")
            current = current[key]

        logger.info(f"提取结果: {current} (类型: {type(current)})")
        return current

    def assert_result(self, case, res):
        if "validate" not in case:
            logger.info("用例没有断言配置")
            return
            
        logger.info(f"开始执行断言，断言配置: {case['validate']}")
        
        for item in case["validate"]:
            for method, expect in item.items():
                if method == "equals":
                    for field, val in expect.items():
                        logger.info(f"执行equals断言 - 字段: {field}, 期望值: {val}")
                        actual = self.extract_value(res, f"content.{field}")
                        logger.info(f"断言检查 → 字段: {field} | 期望: {val} | 实际: {actual} | 期望类型: {type(val)} | 实际类型: {type(actual)}")
                        
                        # 添加类型转换处理
                        if isinstance(val, str) and isinstance(actual, int):
                            try:
                                val = int(val)
                            except ValueError:
                                pass
                        elif isinstance(val, int) and isinstance(actual, str):
                            try:
                                actual = int(actual)
                            except ValueError:
                                pass
                        
                        logger.info(f"类型转换后 → 期望: {val} | 实际: {actual}")
                        assert actual == val, f"断言失败 → 字段: {field} | 期望: {val} | 实际: {actual}"

    @allure.step("执行用例")
    def send_request(self, case):
        case_name = case.get('name', '未知用例')
        logger.info(f"【{case_name}】开始执行")

        method = case["method"].upper()
        url = self.standard_url(case)

        headers = self.replace_vars(case.get("headers", {}), case.get("name", ""))
        params = self.replace_vars(case.get("params"), case.get("name", ""))
        data = self.replace_vars(case.get("data"), case.get("name", ""))
        json_data = self.replace_vars(case.get("json"), case.get("name", ""))

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
        
        # 返回响应对象
        return res