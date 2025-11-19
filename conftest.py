import json
import pytest


def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="test", help="运行环境: dev/test/pre/prod")


@pytest.fixture(scope="session")
def env_config(request):
    env = request.config.getoption("--env")
    with open("config/env_config.yaml", encoding="utf-8") as f:
        envs = json.load(f)
    return envs[env]
