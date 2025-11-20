# tests/test_api.py
import pytest
import allure
from utils.request_util import RequestUtil
from utils.log import logger

# 使用 cases fixture 获取测试数据
def test_api(cases, env_config):
    request = RequestUtil()
    request.base_url = env_config["base_url"]
    
    # 动态生成测试用例
    # 注意：由于 pytest 的参数化是在收集阶段执行的，而 fixture 是在执行阶段执行的
    # 这里我们不能直接用 fixture 来做参数化。
    # 但是，我们可以用 pytest_generate_tests 钩子，或者简单地在函数内部遍历（虽然这样会变成一个大用例）
    # 或者，我们保持原来的参数化方式，但是把读取逻辑封装好。
    
    # 修正方案：为了保持报告的独立性，我们还是需要在模块级别读取用例，
    # 但是我们可以复用 conftest 中的逻辑，或者直接在这里读取。
    # 考虑到最佳实践，我们通常会在 conftest 中定义一个 hook 来生成参数化，
    # 或者保留原来的 yaml 读取方式但做得更优雅。
    
    # 鉴于当前架构，最简单的改进是保持 parameterize，但移除全局变量污染
    pass

# 重新实现，为了支持参数化，我们需要在模块级别加载数据，但要优雅一点
import yaml
import os

def load_cases():
    case_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "api_cases.yaml")
    try:
        with open(case_path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"加载用例失败: {e}")
        return []

cases_data = load_cases()
# tests/test_api.py
import pytest
import allure
from utils.request_util import RequestUtil
from utils.log import logger

# 使用 cases fixture 获取测试数据
def test_api(cases, env_config):
    request = RequestUtil()
    request.base_url = env_config["base_url"]
    
    # 动态生成测试用例
    # 注意：由于 pytest 的参数化是在收集阶段执行的，而 fixture 是在执行阶段执行的
    # 这里我们不能直接用 fixture 来做参数化。
    # 但是，我们可以用 pytest_generate_tests 钩子，或者简单地在函数内部遍历（虽然这样会变成一个大用例）
    # 或者，我们保持原来的参数化方式，但是把读取逻辑封装好。
    
    # 修正方案：为了保持报告的独立性，我们还是需要在模块级别读取用例，
    # 但是我们可以复用 conftest 中的逻辑，或者直接在这里读取。
    # 考虑到最佳实践，我们通常会在 conftest 中定义一个 hook 来生成参数化，
    # 或者保留原来的 yaml 读取方式但做得更优雅。
    
    # 鉴于当前架构，最简单的改进是保持 parameterize，但移除全局变量污染
    pass

# 重新实现，为了支持参数化，我们需要在模块级别加载数据，但要优雅一点
import yaml
import os

def load_cases():
    case_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "api_cases.yaml")
    try:
        with open(case_path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"加载用例失败: {e}")
        return []

cases_data = load_cases()

@pytest.mark.parametrize("case", cases_data, ids=[c.get('name', f'case_{i}') for i, c in enumerate(cases_data)])
def test_execute_request(case, env_config):
    """
    执行接口自动化测试用例
    """
    # 动态设置 Allure 标题
    allure.dynamic.title(case.get("name", "未知用例"))
    allure.dynamic.description(f"URL: {case.get('url')}\nMethod: {case.get('method')}")
    
    # 初始化 RequestUtil 时传入 env_config
    request = RequestUtil(env_config)
    # request.base_url = env_config["base_url"] # 这一行可以删除了，因为在 __init__ 中已经设置了
    
    # 执行请求
    request.send_request(case)