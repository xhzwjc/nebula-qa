import os
os.system("pytest -s --env=test --alluredir=reports/allure-results --clean-alluredir")
os.system("allure serve reports/allure-results")