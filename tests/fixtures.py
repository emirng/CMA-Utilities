import pytest

# CMA webservice host and port for test
cma_ws_host, cma_ws_port = 'localhost', 5000

driver = None


@pytest.fixture
def webdriver():
    global driver  # store in global because it takes too long to start up
    if not driver:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        options = Options()
        options.BinaryLocation = '/usr/bin/chromium-browser'
        options.add_argument('--headless')

        class Webdriver(webdriver.Chrome):

            def path_get(self, path):
                base = 'http://{0}:{1}'.format(cma_ws_host, cma_ws_port)
                super().get(base + path)

            @property
            def current_path(self):
                base = 'http://{0}:{1}'.format(cma_ws_host, cma_ws_port)
                assert self.current_url.startswith(base)
                return self.current_url[len(base):]

        driver = Webdriver(options=options)

    yield driver
