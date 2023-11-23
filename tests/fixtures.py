import pytest

# CMA webservice host and port for test
cma_ws_host, cma_ws_port = 'localhost', 5000


@pytest.fixture
def setup(request, pytestconfig, httpserver):
    from pytest_flask.fixtures import LiveServer
    from main import app

    httpserver.expect_request(
        '/oauth/token').respond_with_json({'access_token': 'x'})

    # --- mock camunda api tasks/search
    keys = ['id', 'name', 'creationDate', 'completionDate', 'assignee',
            'taskState', 'processDefinitionKey', 'processInstanceKey', 'formKey']

    items_values = [
        [
            '6755399441084844', "Decide what's for dinner", '2022-02-02T12:12:12.000+0000',
            '2022-02-02T12:12:12.000+0000', 'Lisa', 'COMPLETED', '2251799813703085',
            '6755399441084839', '1:2:3',
        ],
        [
            '6755399441084841', "Decide what's for dinner", '2022-02-02T12:12:12.000+0000',
            None, None, 'CREATED', '2251799813703011',
            '6755399441084822', '4:5:6',
        ],
    ]
    items = [{k: v for k, v in zip(keys, values)} for values in items_values]

    httpserver.expect_request('/v1/tasks/search').respond_with_json(items)
    # ---

    # --- mock camunda api process-instances/search
    keys = ['key', 'processVersion', 'bpmnProcessId', 'startDate', 'state', 'processDefinitionKey',
            'tenantId', ]

    items_values = [
        [
            '2251799813703087', '1', 'template-test', "2022-02-02T12:12:12.000+0000", 'ACTIVE',
            '2251799813703085',  '<default>',
        ],
        [
            '2251799813703081', '2', 'template-test-2', None, 'ACTIVE',
            '2251799813703082',  '<default>',
        ]
    ]
    items = [{k: v for k, v in zip(keys, values)} for values in items_values]
    httpserver.expect_request(
        '/v1/process-instances/search').respond_with_json({'items': items})
    # ---

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
        options.add_argument("window-size=1800,900")

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
