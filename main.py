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

    return render_template('tasks.j2', items=items)


@app.route('/task/<task_id>/complete', methods=['POST'])
def task_complete(task_id):
    call('PATCH', '/v1/tasks/{0}/complete'.format(task_id))
    return redirect('/task')


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


app.run(debug=True)
