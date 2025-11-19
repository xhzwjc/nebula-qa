import os


def main() -> None:
    os.system("pytest -s --env=test --alluredir=reports/allure-results --clean-alluredir")
    os.system("allure serve reports/allure-results")


if __name__ == "__main__":
    main()
