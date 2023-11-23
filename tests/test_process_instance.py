from tests.fixtures import setup
from tests.fixtures import webdriver


def test_process_instance_search_view(setup, webdriver):
    """
        List process-instances at process-instance search view.
    """

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


def test_view_single_process_instance_and_its_tasks_and_variables(setup, webdriver):
    key = '2251799813703087'

    # --- mock camunda api
    httpserver = setup[1]

    data = {
        'key': key,
        'processVersion': '1',
        'bpmnProcessId': 'template-test',
        'startDate': '2022-02-02\n12:12 +0000',
        'state': 'ACTIVE',
        'processDefinitionKey': '2251799813703085',
        'tenantId': '<default>',
    }

    httpserver.expect_request(
        f'/v1/process-instances/{key}').respond_with_json(data)

    httpserver.expect_request(
        '/v1/variables/search', method="POST", json={'processInstanceKey': key}).respond_with_json(
        {
            "items": [{
                'key': '1',
                'processInstanceKey': '2',
                'scopeKey': '3',
                'name': '4',
                'value': '5',
                'truncated': '6',
                'tenantId': '7',
            }]})
    # ---

    webdriver.path_get(f'/process-instance/{key}')

    actual = list()
    for table in webdriver.find_elements('xpath', "//table"):
        inner_actual = list()
        for tr in table.find_elements('xpath', './tbody/tr'):
            item = [e.text for e in tr.find_elements('xpath', './th | ./td')]
            inner_actual.append(item)
        actual.append(inner_actual)

    expected = [[['Key', '2251799813703087'], ['Process version', '1'], ['BPMN Process id', 'template-test'], ['Start date', '2022-02-02 12:12 +0000'], ['State', 'ACTIVE'], ['Process definition key', '2251799813703085'], ['Tenant id', '']], [['Id', 'Name', 'Creation data', 'Completion data', 'Assignee', 'Task state', 'Process definition key', 'Process instance key', 'Form', ''], ['6755399441084844', "Decide what's for dinner", '2022-02-02T12:12:12.000+0000',
                                                                                                                                                                                                                                                                                                                                                                                               '2022-02-02T12:12:12.000+0000', 'Lisa', 'COMPLETED', '2251799813703085', '6755399441084839', 'Goto form', ''], ['6755399441084841', "Decide what's for dinner", '2022-02-02T12:12:12.000+0000', 'None', 'Unassigned\nAssign', 'CREATED', '2251799813703011', '6755399441084822', 'Goto form', 'Complete']], [['Key', 'Process instance key', 'Scope key', 'Name', 'Value', 'Truncated', 'Tenant id'], ['1', '2', '3', '4', '5', '6', '7']]]

    assert actual == expected


def test_process_instance_delete_at_search_view(setup, webdriver):
    """
        Make sure delete process-instances at process-instance search view actual sends
        the delete request to rest.
    """

    webdriver.path_get('/process-instance')

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
    tr = find_table_row(webdriver, 'Key', pi_id)

    for delete_button in tr.find_elements('xpath', "./td/form/button[text()='Delete']"):
        delete_button.click()

    assert delete_request_handler not in httpserver.oneshot_handlers


def find_table_row(webdriver, column, value):
    for table in webdriver.find_elements('xpath', '//table'):
        for e, th in enumerate(table.find_elements('xpath', './tbody/tr[1]/th'), 1):
            if th.text == column:
                for tr in table.find_elements(
                        'xpath', f"./tbody/tr/td[{e}]/a[text()='{value}']/parent::td/parent::tr"):
                    return tr
