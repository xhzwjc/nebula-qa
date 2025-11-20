import pytest
import os
import sys

def run():
    # 确保当前目录在sys.path中
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # 定义报告目录
    report_dir = "reports/allure-results"
    
    # 构建pytest参数
    args = [
        "-s",
        "--env=test",
        f"--alluredir={report_dir}",
        "--clean-alluredir"
    ]
    
    print("开始执行测试...")
    # 执行测试
    exit_code = pytest.main(args)
    
    if exit_code == 0:
        print("测试执行成功！")
    else:
        print(f"测试执行完成，退出码: {exit_code}")
        
    # 生成并打开报告 (可选，CI环境中通常不需要这一步)
    # 注意：os.system会阻塞，直到手动关闭allure服务
    try:
        print("正在生成Allure报告...")
        os.system(f"allure serve {report_dir}")
    except KeyboardInterrupt:
        print("停止Allure服务")

if __name__ == '__main__':
    run()