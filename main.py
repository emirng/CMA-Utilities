import requests
import json
from flask import Flask, render_template, redirect, request, session
from rest import call
from common import date_output
from cma_secrets import app_secret_key

app = Flask(__name__)
app.secret_key = app_secret_key


@app.route('/')
def index():
    return redirect('/process-instance')


@app.route('/process-instance')
def process():
    data = call('POST', '/v1/process-instances/search')
    items = data.json()['items']
    for item in items:
        for key in ['startDate']:
            item[key] = date_output(item[key])

    alert = session.pop('alert', None)
    return render_template('process-instances.j2', items=items, alert=alert)


@app.route('/process-instance/<process_key>')
def process_instance(process_key):
    data = call('GET', '/v1/process-instances/{0}'.format(process_key))
    item = data.json()

    tasks = call('POST', '/v1/tasks/search',
                 data={'processInstanceKey': process_key})
    tasks = tasks.json()
    for task in tasks:
        if task['formKey'] is not None:
            task['formId'] = task['formKey'].split(':')[2]

    variables = call('POST', '/v1/variables/search',
                     data={'processInstanceKey': process_key})
    variables = variables.json()['items']

    return render_template('process-instance.j2', process_instance=item, tasks=tasks, variables=variables)


@app.route('/process-instance/<process_key>/delete', methods=['POST'])
def process_delete(process_key):
    data = call('DELETE', '/v1/process-instances/{0}'.format(process_key))

    if data.status_code == 400:
        session['alert'] = {
            'strong': 'Delete failed!',
            'text': data.json()['message'],
            'type': 'danger'
        }

    return redirect('/process-instance')


@app.route('/task')
def task():
    data = call('POST', '/v1/tasks/search')
    items = data.json()
    for item in items:
        for key in ['creationDate', 'completionDate']:
            item[key] = date_output(item[key])
        if item['formKey'] is not None:
            item['formId'] = item['formKey'].split(':')[2]

    return render_template('tasks.j2', items=items)


@app.route('/task/<task_id>/complete', methods=['POST'])
def task_complete(task_id):
    call('PATCH', '/v1/tasks/{0}/complete'.format(task_id))
    return redirect(request.form.get('redirect_to', '/task'))


@app.route('/task/<task_id>/assign', methods=['GET', 'POST'])
def task_assign(task_id):

    if request.method == 'POST':
        data = {
            "assignee": request.form['assignee'],
            "allowOverrideAssignment": True
        }
        response = call('PATCH', '/v1/tasks/'+task_id+'/assign', data=data)
        return redirect('/task')

    elif request.method == 'GET':
        return render_template('assign.j2')


@app.route('/variable')
def variable():
    data = call('POST', '/v1/variables/search')
    items = data.json()['items']
    return render_template('variables.j2', items=items)


@app.route('/form/<form_id>/<process_definition_key>', methods=['GET', 'POST'])
def form(form_id, process_definition_key):
    response = call(
        'GET', '/v1/forms/{0}?processDefinitionKey={1}'.format(form_id, process_definition_key))
    schema = json.loads(response.json()['schema'])

    if request.method == 'POST':

        data = {
            'variables': []
        }

        for component in schema['components']:
            if component['type'] == 'radio':
                key = component['key']
                data['variables'].append(
                    {'name': key, 'value': request.form[key]})

        call(
            'PATCH', '/v1/tasks/{0}/complete'.format(request.args['task-id']), data=data)

        return redirect('/task')

    elif request.method == 'GET':

        components = schema['components']

        for component in components:
            if component['type'] == 'radio':
                for value in component['values']:
                    # TODO: this solution makes our example process to work.
                    #      look over so every value works
                    value['rvalue'] = '&quot;{0}&quot;'.format(value['value'])

        return render_template('form.j2', components=components, task=request.args.get('task-id'))


if __name__ == '__main__':
    app.config["AUTH_SERVER"] = 'https://login.cloud.camunda.io/oauth/token'
    app.config["REST_SERVER"] = 'https://{region_id}.{audience}.camunda.io/{cluster_id}'
    app.run()
