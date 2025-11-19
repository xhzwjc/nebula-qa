import argparse
import importlib.util
import shutil
import subprocess
import sys


def _has_allure_pytest() -> bool:
    return importlib.util.find_spec("allure_pytest") is not None


def main() -> None:
    parser = argparse.ArgumentParser(description="运行接口自动化用例")
    parser.add_argument("--env", default="test", help="指定运行环境，默认 test")
    parser.add_argument(
        "--skip-allure",
        action="store_true",
        help="仅运行pytest，不生成/启动 Allure 报告",
    )
    args = parser.parse_args()

    pytest_cmd = [
        "pytest",
        "-s",
        f"--env={args.env}",
    ]

    allure_enabled = False
    if not args.skip_allure and _has_allure_pytest():
        allure_enabled = True
        pytest_cmd.extend(["--alluredir", "reports/allure-results", "--clean-alluredir"])
    elif not args.skip_allure:
        print("未检测到 allure-pytest 插件，已跳过 Allure 报告生成。")

    result = subprocess.run(pytest_cmd, check=False)
    if result.returncode != 0:
        sys.exit(result.returncode)

    if allure_enabled:
        allure_cli = shutil.which("allure")
        if allure_cli is None:
            print("未找到 allure 命令，无法自动打开报告。")
            return
        subprocess.run([allure_cli, "serve", "reports/allure-results"], check=False)


if __name__ == "__main__":
    main()
