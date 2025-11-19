# tests/test_api.py
import pytest
import yaml
import allure

from utils.log import logger
from utils.request_util import RequestUtil

# 读取用例
with open("data/api_cases.yaml", encoding="utf-8") as f:
    cases = yaml.safe_load(f)

# 参数化测试用例
@pytest.mark.parametrize("case", cases, ids=[case.get('name', f'case_{i}') for i, case in enumerate(cases)])
def test_api(case, env_config):   # ← 这里必须保留两个参数
    request = RequestUtil()
    request.base_url = env_config["base_url"]
    
    # 执行请求并获取响应
    response = request.send_request(case)
    
    # 显示响应结果到控制台
    print(f"\n{'='*50}")
    print(f"用例名称: {case.get('name', '未知用例')}")
    print(f"请求URL: {request.base_url}{case.get('url', '')}")
    print(f"请求方法: {case.get('method', '')}")
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    print(f"{'='*50}\n")