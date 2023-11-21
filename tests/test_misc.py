from tests.fixtures import setup
from tests.fixtures import webdriver


def test_fallback_to_process_instance(setup, webdriver):
    """
        Always redirect to process-instance if no resource has been specified.
    """
    webdriver.path_get('')  # <-- no resource specified (empty string)
    assert webdriver.current_path == '/process-instance'
