from tests.fixtures import setup
from tests.fixtures import webdriver


def test_variable_search_view(setup, webdriver):
    """
        List variables at variable search view.
    """

    # --- mock camunda api variables/search
    httpserver = setup[1]
    keys = ['key', 'processInstanceKey', 'scopeKey',
            'name', 'value', 'truncated',  'tenantId', ]

    items_values = [
        ['1', '2251799813703087', '2', 'meal', 'chicken', '3', '4'],
        ['1', '2251799813703082', '2', 'meal', 'meat', '3', '4']


    ]
    items = [{k: v for k, v in zip(keys, values)} for values in items_values]
    httpserver.expect_request(
        '/v1/variables/search').respond_with_json({'items': items})
    # ---

    # get variables
    webdriver.path_get('/variable')

    # make actual
    actual = list()
    for tr in webdriver.find_elements('xpath', '//tr'):
        item = [e.text for e in tr.find_elements('xpath', './th | ./td')]
        actual.append(item)

    # define expected
    expected = [
        ['Key', 'Process instance key', 'Scope key',
            'Name', 'Value', 'Truncated', 'Tenant id'],
        ['1', '2251799813703087', '2', 'meal', 'chicken', '3', '4'],
        ['1', '2251799813703082', '2', 'meal', 'meat', '3', '4']
    ]

    # assert
    assert actual == expected
