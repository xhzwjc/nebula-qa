"""High level API test covering all YAML-driven cases."""
import json
import pytest
import allure

from utils.request_util import RequestUtil

with open("data/api_cases.yaml", encoding="utf-8") as f:
    cases = json.load(f)


@pytest.mark.parametrize("case", cases)
def test_api(case, env_config):
    request = RequestUtil()
    request.base_url = env_config["base_url"]
    request.timeout = env_config.get("timeout", 30)
    request.send_request(case)
