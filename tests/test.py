# this file is to test around with tests

import pytest
import requests


@pytest.fixture(scope="session")
def app():
    from main import app
    return app


@pytest.mark.usefixtures('live_server')
def test():
    r = requests.get('http://localhost.localdomain:5000/task/1/assign')
    assert r.status_code == 200
