import pytest

# CMA webservice host and port for test
cma_ws_host, cma_ws_port = 'localhost', 5000


@pytest.fixture
def setup(request, pytestconfig, httpserver):
    from pytest_flask.fixtures import LiveServer
    from main import app

    httpserver.expect_request(
        '/oauth/token').respond_with_json({'access_token': 'x'})

    app.config['AUTH_SERVER'], app.config['REST_SERVER'] = [
        'http://{0}:{1}'.format(httpserver.host, httpserver.port)] * 2
    app.config['DEBUG'] = pytestconfig.getoption('--cma-ws-debug')

    server = LiveServer(app, cma_ws_host, cma_ws_port, wait=5)
    server.start()

    request.addfinalizer(server.stop)
    yield server, httpserver, app


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
