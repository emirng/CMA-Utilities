from tests.fixtures import setup
from tests.fixtures import webdriver


def test_task_search_view(setup, webdriver):

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
            '6755399441084841',
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
            'Unassigned\nAssign', 'COMPLETED', '2251799813703085', '6755399441084839', 'Goto form', ''],
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
