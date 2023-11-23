from tests.fixtures import setup
from tests.fixtures import webdriver


def test_task_search_view(setup, webdriver):

    # get process instances
    webdriver.path_get('/task')

    # make actual
    actual = list()
    for tr in webdriver.find_elements('xpath', '//tr'):
        item = [e.text for e in tr.find_elements('xpath', './th | ./td')]
        actual.append(item)

    # define expected
    expected = [
        ['Id', 'Name', 'Creation data', 'Completion data', 'Assignee', 'Task state',
            'Process definition key', 'Process instance key', 'Form', ''],
        ['6755399441084844', "Decide what's for dinner", '2022-02-02\n12:12 +0000', '2022-02-02\n12:12 +0000',
            'Lisa', 'COMPLETED', '2251799813703085', '6755399441084839', 'Goto form', ''],
        ['6755399441084841', "Decide what's for dinner", '2022-02-02\n12:12 +0000', '-',
            'Unassigned\nAssign', 'CREATED', '2251799813703011', '6755399441084822', 'Goto form', 'Complete']
    ]

    # assert
    assert actual == expected


def test_task_complete_at_search_view(setup, webdriver):

    # task to complete
    task_id = '6755399441084841'

    # --- mock camunda api tasks/search
    httpserver = setup[1]

    keys = ['id', 'name', 'creationDate', 'completionDate', 'assigne',
            'taskState', 'processDefinitionKey', 'processInstanceKey', 'formKey']

    items_values = [
        [
            '6755399441084844',
            "Decide what's for dinner",
            "2022-02-02T12:12:12.000+0000",
            "2022-02-02T12:12:12.000+0000",
            'Lisa',
            'COMPLETED',
            '2251799813703085',
            '6755399441084839',
            "1:1:1",
        ],
        [
            task_id,
            "Decide what's for dinner",
            "2022-02-02T12:12:12.000+0000",
            None,
            'Lisa',
            'CREATED',
            '2251799813703011',
            '6755399441084822',
            "1:1:1",
        ],


    ]
    items = [{k: v for k, v in zip(keys, values)} for values in items_values]

    httpserver.expect_request(
        '/v1/tasks/search').respond_with_json(items)
    # ---

    # --- mock camunda api endpoint for complete task (for the specific task)
    complete_request_handler = httpserver.expect_oneshot_request(
        f'/v1/tasks/{task_id}/complete', method='PATCH')
    complete_request_handler.respond_with_json({})
    # ---

    # --- fetch tasks and click on the complete button for the specific task to delete
    webdriver.path_get('/task')
    tr = find_table_row(webdriver, 'Id', task_id)
    for complete_button in tr.find_elements('xpath', "./td/form/button[text()='Complete']"):
        complete_button.click()
    # ---

    # assert that the call was made to camunda (if gone from oneshot handles that means it was handled)
    assert complete_request_handler not in httpserver.oneshot_handlers


def test_goto_task_form_from_task_search_view(setup, webdriver):
    task_id = '6755399441084844'
    webdriver.path_get('/task')
    tr = find_table_row(webdriver, 'Id', task_id)
    anchor_goto_form = tr.find_elements(
        'xpath', "./td/a[text()='Goto form']")[0]
    anchor_goto_form.click()

    assert webdriver.current_path == f'/form/3/2251799813703085?process-instance=6755399441084839&task-id={task_id}'


def test_from_task_form_submit_variables(setup, webdriver):

    task_id = '6755399441084844'
    form_id = '3'
    process_definition_key = '6755399441084839'
    process_instance = '6755399441084839'

    httpserver = setup[1]

    # --- mock camunda api endpoint for getting form data
    url = f'/v1/forms/{form_id}'
    form_request_handler = httpserver.expect_request(
        url, query_string=f'processDefinitionKey={process_definition_key}',  method='GET')
    form_request_handler.respond_with_json(
        {'schema': '{"components":[ {"key": "test-radio-key", "type":"radio", "values":[ {"value":"test-radio-value-1", "label":"test-radio-label-1"  }, {"value":"test-radio-value-2", "label":"test-radio-label-2"  }  ], "validate":{"required":true}  }  ]}'})
    # ---

    # --- mock camunda api endpoint for submit variables during complete task
    data = {'variables': [
        {'name': 'test-radio-key', 'value': '"test-radio-value-2"'}]}

    submit_request_handler = httpserver.expect_oneshot_request(
        f'/v1/tasks/{task_id}/complete', method='PATCH', json=data)
    submit_request_handler.respond_with_json({})
    # ---

    webdriver.path_get(
        f'/form/{form_id}/{process_definition_key}?process-instance={process_instance}&task-id={task_id}')

    # click and select test-radio-label-2
    webdriver.find_elements(
        'xpath', "//*[text()='test-radio-label-2']")[0].click()

    # submit form
    webdriver.find_elements(
        'xpath', "//button[text()='Submit and complete task']")[0].click()

    # assert that the call was made to camunda (if gone from oneshot handles that means it was handled)
    assert submit_request_handler not in httpserver.oneshot_handlers


def test_assign_user_to_unassigned_task(setup, webdriver):

    httpserver = setup[1]

    # task to assign and to what user
    task_id = '6755399441084841'
    username = 'Emil'

    # --- mock camunda api endpoint for assign (for the specific task)
    data = {
        'assignee': username,
        'allowOverrideAssignment': True
    }
    assign_request_handler = httpserver.expect_oneshot_request(
        f'/v1/tasks/{task_id}/assign', method='PATCH', json=data)
    assign_request_handler.respond_with_json({})
    # ---

    # part 1: go to task page and click assign for that specific task to assign new user to
    webdriver.path_get('/task')
    tr = find_table_row(webdriver, 'Id', task_id)
    for assign_anchor in tr.find_elements('xpath', "./td/a[text()='Assign']"):
        assign_anchor.click()
    assert webdriver.current_path == f'/task/{task_id}/assign'

    # part 2:  enter username in form and press sumbit
    _input = webdriver.find_elements(
        'xpath', "//label[text()='Assignee']/parent::div/input")[0]
    _input.send_keys(username)

    submit_button = _input.find_elements(
        'xpath', "./parent::div/parent::form/button[text()='Submit']")[0]
    submit_button.click()

    # assert that the call was made to camunda (if gone from oneshot handles that means it was handled)
    assert assign_request_handler not in httpserver.oneshot_handlers


def find_table_row(webdriver, column, value):
    for table in webdriver.find_elements('xpath', '//table'):
        for e, th in enumerate(table.find_elements('xpath', './tbody/tr[1]/th'), 1):
            if th.text == column:

                # check for value found inside anchor-element inside the td-element
                for tr in table.find_elements(
                        'xpath', f"./tbody/tr/td[{e}]/a[text()='{value}']/parent::td/parent::tr"):
                    return tr

                # check for value found directly found inside the td-element
                for tr in table.find_elements(
                        'xpath', f"./tbody/tr/td[{e}][text()='{value}']/parent::tr"):
                    return tr

    raise Exception()
