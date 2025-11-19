# tests/test_api.py   ← 直接替换整个文件内容
import pytest
import yaml
import allure
from utils.request_util import RequestUtil

# 读取用例
with open("data/api_cases.yaml", encoding="utf-8") as f:
    cases = yaml.safe_load(f)

# 正确！两个参数都要写进 parametrize
@pytest.mark.parametrize("case", cases)
def test_api(case, env_config):   # ← 这里必须保留两个参数
    request = RequestUtil()
    request.base_url = env_config["base_url"]   # 现在 env_config 才是真正的环境配置
    request.send_request(case)