import pytest
import yaml
import os
from utils.log import logger

def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="test", help="运行环境: dev/test/pre/prod")

@pytest.fixture(scope="session")
def env_config(request):
    env = request.config.getoption("--env")
    config_path = os.path.join(os.path.dirname(__file__), "config", "env_config.yaml")
    
    logger.info(f"加载环境配置: {env}")
    
    with open(config_path, encoding="utf-8") as f:
        envs = yaml.safe_load(f)
        config = envs.get(env)
        
        if not config:
            raise ValueError(f"环境配置 {env} 不存在")
            
        # 清理base_url
        if 'base_url' in config:
            base_url = config['base_url']
            if isinstance(base_url, str):
                base_url = base_url.replace('`', '').strip()
                config['base_url'] = base_url
                
        logger.info(f"当前环境Base URL: {config.get('base_url')}")
        return config

@pytest.fixture(scope="session")
def cases():
    """加载所有测试用例"""
    case_path = os.path.join(os.path.dirname(__file__), "data", "api_cases.yaml")
    logger.info(f"加载测试用例: {case_path}")
    
    with open(case_path, encoding="utf-8") as f:
        cases_data = yaml.safe_load(f)
        
    logger.info(f"共加载 {len(cases_data)} 条用例")
    return cases_data

from utils.request_util import RequestUtil
from utils.yaml_util import write_extract

@pytest.fixture(scope="session", autouse=True)
def login(env_config):
    """
    全局登录 fixture，自动执行登录并保存 token
    """
    logger.info("========== 开始执行全局登录 ==========")
    
    # 构造登录用例数据
    login_case = {
        "name": "全局登录",
        "method": "POST",
        "url": "/auth/app/login",
        "headers": {
            "Content-Type": "application/json"
        },
        "json": {
            "mobile": env_config.get("mobile"),
            "code": env_config.get("code"),
            "type": 1
        }
    }
    
    request = RequestUtil(env_config)
    try:
        # 发送登录请求
        res = request.send_request(login_case)
        
        # 检查响应状态
        if res.status_code != 200:
            logger.error(f"登录失败，状态码: {res.status_code}")
            return
            
        # 尝试提取 token
        # 假设 token 在 content.data.token 或 content.token
        try:
            res_json = res.json()
            # 优先尝试 data.token
            token = res_json.get("data", {}).get("access_token")
            if not token:
                # 其次尝试直接在根节点
                token = res_json.get("token")
                
            if token:
                logger.info(f"登录成功，获取到 Token: {token[:10]}******")
                write_extract({"token": token})
            else:
                logger.error(f"登录响应中未找到 Token: {res.text}")
                
        except Exception as e:
            logger.error(f"解析登录响应异常: {e}")
            
    except Exception as e:
        logger.error(f"登录请求执行异常: {e}")
    finally:
        logger.info("========== 全局登录结束 ==========\n")