from tests.fixtures import webdriver
from selenium.common.exceptions import WebDriverException


def test(webdriver):
    try:
        webdriver.path_get('/test')
    except WebDriverException:  # <-- this is expected to happen since this test doesn't
        pass  # setup cma-utils

    assert webdriver.current_path == '/test'
