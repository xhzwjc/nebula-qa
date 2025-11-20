# utils/request_util.py
import requests
import allure
import re
from utils.yaml_util import read_extract, write_extract
from utils.log import logger

class RequestUtil:
    def __init__(self, env_config=None):
        self.session = requests.Session()
        self.env_config = env_config or {}
        self.base_url = self.env_config.get("base_url", "")

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
                
                # 优先级1: 从extract文件中读取 (接口关联变量)
                value = read_extract(key)
                
                # 优先级2: 从环境配置中读取 (环境相关变量，如mobile, code)
                if value is None and key in self.env_config:
                    value = self.env_config[key]
                
                if value is None:
                    # 如果变量未找到，记录警告并返回原字符串，避免直接崩溃
                    # 特殊处理：如果是登录相关的用例，可能不需要token，忽略警告
                    if "登录" in case_name and key == "token":
                         return obj
                    
                    logger.warning(f"变量 ${{{key}}} 未找到，将保持原样。用例: {case_name}")
                    return obj
                    
                return obj.replace(m.group(0), str(value))
            return obj
        return obj  # 非字符串/字典/列表类型直接返回

    def standard_url(self, case):
        url = case["url"]
        if case.get("path_params"):
            for k, v in case["path_params"].items():
                v = self.replace_vars(v, case.get("name", ""))
                url = url.replace(f"{{{k}}}", str(v))
        
        if url.startswith("http"):
            return url
        return self.base_url + url

    def extract_value(self, res, expr):
        """通用提取方法"""
        # logger.debug(f"提取表达式: {expr}")
        if not expr.startswith("content."):
            return None

        path = expr.replace("content.", "").split(".")
        try:
            data = res.json()
        except Exception as e:
            logger.error(f"响应非JSON格式，无法提取: {res.text[:100]}")
            return None

        current = data
        try:
            for key in path:
                if isinstance(current, list):
                    try:
                        key = int(key)
                        current = current[key]
                    except (ValueError, IndexError):
                         logger.error(f"提取失败: 列表索引错误 {key}")
                         return None
                elif isinstance(current, dict):
                    if key not in current:
                         logger.error(f"提取失败: 键 {key} 不存在")
                         return None
                    current = current[key]
                else:
                    logger.error(f"提取失败: 无法在 {type(current)} 中查找 {key}")
                    return None
        except Exception as e:
            logger.error(f"提取过程发生异常: {e}")
            return None

        logger.info(f"提取结果: {expr} = {current}")
        return current

    def assert_result(self, case, res):
        if "validate" not in case:
            return
            
        logger.info(f"执行断言: {case['validate']}")
        
        for item in case["validate"]:
            for method, expect in item.items():
                if method == "equals":
                    for field, val in expect.items():
                        actual = self.extract_value(res, f"content.{field}")
                        
                        # 类型转换处理
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
                        
                        if actual != val:
                            logger.error(f"断言失败 - 字段: {field} | 期望: {val} ({type(val)}) | 实际: {actual} ({type(actual)})")
                            raise AssertionError(f"断言失败: {field} 期望 {val}, 实际 {actual}")
                        else:
                            logger.info(f"断言通过 - 字段: {field} | 值: {actual}")

    @allure.step("执行接口请求")
    def send_request(self, case):
        case_name = case.get('name', '未知用例')
        logger.info(f"========== 开始执行: {case_name} ==========")
        
        try:
            # 替换变量
            case = self.replace_vars(case, case_name)
            
            # 构造URL
            url = self.standard_url(case)
            
            # 准备请求参数
            method = case.get("method", "GET").upper()
            headers = case.get("headers", {})
            params = case.get("params", {})
            json_data = case.get("json", None)
            data = case.get("data", None)
            
            logger.info(f"请求方法: {method}")
            logger.info(f"请求URL: {url}")
            logger.info(f"请求头: {headers}")
            if params:
                logger.info(f"请求参数: {params}")
            if json_data:
                logger.info(f"请求体(JSON): {json_data}")
            if data:
                logger.info(f"请求体(Data): {data}")
            
            # 发送请求
            res = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                data=data
            )
            
            logger.info(f"响应状态码: {res.status_code}")
            try:
                logger.info(f"完整响应内容: {res.json()}")
            except:
                logger.info(f"完整响应内容(Text): {res.text}")
            
            # 提取
            if "extract" in case:
                for var_name, expr in case["extract"].items():
                    value = self.extract_value(res, expr)
                    if value is not None:
                        write_extract({var_name: value})

            # 断言
            self.assert_result(case, res)
            
            return res
            
        except Exception as e:
            logger.error(f"请求执行异常: {e}")
            raise
        finally:
            logger.info(f"========== 结束执行: {case_name} ==========\n")