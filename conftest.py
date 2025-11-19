import pytest
import yaml

def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="test", help="运行环境: dev/test/pre/prod")

@pytest.fixture(scope="session")
def env_config(request):
    env = request.config.getoption("--env")
    with open("config/env_config.yaml", encoding="utf-8") as f:
        envs = yaml.safe_load(f)
        config = envs[env]
        
        # 清理base_url，移除多余的反引号和空格
        if 'base_url' in config:
            base_url = config['base_url']
            if isinstance(base_url, str):
                # 移除所有的反引号和空格
                base_url = base_url.replace('`', '').strip()
                config['base_url'] = base_url
                
        return config