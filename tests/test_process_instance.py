from tests.fixtures import setup
from tests.fixtures import webdriver


def test_process_instance_search_view(setup, webdriver):
    """
        List process-instances at process-instance search view.
    """

    # --- mock camunda api process-instances/search
    httpserver = setup[1]
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

    # get process instances
    webdriver.path_get('/process-instance')

    # make actual
    actual = list()
    for tr in webdriver.find_elements('xpath', '//tr'):
        item = [e.text for e in tr.find_elements('xpath', './th | ./td')]
        actual.append(item)

    # define expected
    expected = [
        ['Key', 'Process version', 'BPMN process id', 'Start date', 'State', 'Process definition key',
         'Tenant id', ''],
        ['2251799813703087', '1', 'template-test', '2022-02-02\n12:12 +0000', 'ACTIVE',
         '2251799813703085', '<default>', 'Delete'],
        ['2251799813703081', '2', 'template-test-2', '-', 'ACTIVE',
         '2251799813703082', '<default>', 'Delete']
    ]

    # assert
    assert actual == expected


def test_process_instance_delete_at_search_view(setup, webdriver):
    """
        Make sure delete process-instances at process-instance search view actual sends
        the delete request to rest.
    """

    # --- mock camunda api process-instances/search
    httpserver = setup[1]
    keys = ['key', 'processVersion', 'bpmnProcessId', 'startDate', 'state', 'processDefinitionKey',
            'tenantId', ]

    pi_id = '2251799813703081'  # the process id we want to delete

    items_values = [
        [
            '2251799813703087', '1', 'template-test', "2022-02-02T12:12:12.000+0000", 'ACTIVE',
            '2251799813703085',  '<default>',
        ],
        [
            pi_id, '2', 'template-test-2', None, 'ACTIVE',
            '2251799813703082',  '<default>',
        ]
    ]
    items = [{k: v for k, v in zip(keys, values)} for values in items_values]
    httpserver.expect_request(
        '/v1/process-instances/search').respond_with_json({'items': items})
    # ---

    # --- mock camunda api delete process-instance (for a specific process-instance)
    delete_request_handler = httpserver.expect_oneshot_request(
        f'/v1/process-instances/{pi_id}', method='DELETE')
    delete_request_handler.respond_with_json({})
    # ---

    # get process instances and delete second row button
    webdriver.path_get('/process-instance')
    webdriver.find_elements('css selector', 'button')[1].click()  # TODO: use a selector to find row with the correct process instance id and find its delete button by the actual label of the button.

    assert delete_request_handler not in httpserver.oneshot_handlers
