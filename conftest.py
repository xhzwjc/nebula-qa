import pytest

from utils.yaml_util import load_data_file


def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="test", help="运行环境: dev/test/pre/prod")


@pytest.fixture(scope="session")
def env_config(request):
    env = request.config.getoption("--env")
    envs = load_data_file("config/env_config.yaml") or {}
    if env not in envs:
        raise KeyError(f"未知环境: {env}")
    return envs[env]
