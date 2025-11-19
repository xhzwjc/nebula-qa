"""High level API test covering all YAML-driven cases."""
import pytest
import allure

from utils.request_util import RequestUtil
from utils.yaml_util import load_data_file

cases = load_data_file("data/api_cases.yaml") or []


@pytest.mark.parametrize("case", cases)
def test_api(case, env_config):
    request = RequestUtil()
    request.base_url = env_config["base_url"]
    request.timeout = env_config.get("timeout", 30)
    request.send_request(case)
