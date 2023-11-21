import os
import requests
from cma_secrets import client_id, client_secret, region_id, cluster_id


def get_auth_server():
    from flask import current_app
    app = current_app
    return app.config["AUTH_SERVER"]


def get_rest_server(region_id, audience, cluster_id):
    from flask import current_app
    app = current_app
    return app.config["REST_SERVER"].format(
        region_id=region_id,
        audience=audience,
        cluster_id=cluster_id,
    )


def get_login_url():
    return get_auth_server()+'/oauth/token'


main_dir = os.path.normpath(os.path.join(os.path.dirname(__file__)))


def get_token(audience, force_refresh=False):
    if not audience in ('operate', 'tasklist'):
        raise ValueError()  # NOTE: add more if needed

    token_file = os.path.join(main_dir, '{0}.token'.format(audience))

    if not force_refresh:
        if os.path.isfile(token_file):
            with open(token_file) as f:
                return f.read()

    login_url = get_login_url()
    response = requests.post(login_url, json={
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": "{0}.camunda.io".format(audience),
        "grant_type": "client_credentials",
    })
    token = response.json()['access_token']

    with open(token_file, 'w') as f:
        f.write(token)

    return token


def call(method, endpoint, data=None):

    if data is None:
        data = {}

    # NOTE: keep expanding list as far as we need it
    audience = {
        '/v1/tasks': 'tasklist',
        '/v1/process-definitions': 'operate',
        '/v1/process-instances': 'operate',
        '/v1/variables': 'operate',
        '/v1/forms': 'tasklist',
    }["/".join(endpoint.split('/')[:3])]

    token = get_token(audience)
    task_url = get_rest_server(region_id, audience, cluster_id) + endpoint

    response = requests.request(method, task_url, headers={
                                'Authorization': 'Bearer {0}'.format(token)}, json=data)

    # TODO: implement catch token expire, if expired try fetch new one (force refresh) and try again (but only try twice)

    return response
