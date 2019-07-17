import json

from flask import Flask, abort, redirect, request, render_template
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

def load_google_cloud():
    """ Loads the libcloud driver to communicate with the Google Cloud API
        for Compute Engine. """
    with open('config.json') as json_file:
        data = json.load(json_file)
        email = data['email']
        config_file = data['config']
        project = data['project']
        ComputeEngine = get_driver(Provider.GCE)
        driver = ComputeEngine(email, config_file, project=project)
        return driver

def get_nodes_by_uuid(uuid):
    nodes = google_cloud_driver.list_nodes()
    return [node for node in nodes if node.uuid == uuid]

def load_chart_urls():
    """ Loads a dictionary from 'charts.json' that maps instance UUIDs
        to an array of URLs to embeddable charts for monitoring. """
    with open('charts.json') as json_file:
        return json.load(json_file)

google_cloud_driver = load_google_cloud()
all_chart_urls = load_chart_urls()
app = Flask(__name__)

def home_with_error(error_msg):
    return redirect('/?error={}'.format(error_msg))

def home_with_success(success_msg):
    return redirect('/?success={}'.format(success_msg))

@app.route('/')
def index():
    servers = google_cloud_driver.list_nodes()
    error = request.args.get('error') # Error message that could be passed in from somewhere
    success = request.args.get('success')
    return render_template('index.html', error=error, success=success, servers=servers)

@app.route('/info/<uuid>')
def info(uuid):
    nodes = get_nodes_by_uuid(uuid)
    if not nodes:
        error_msg = 'Cannot get info for server with UUID {}: Not Found'.format(uuid)
        return home_with_error(error_msg)
    if len(nodes) != 1:
        error_msg = 'Error getting info for server {}: {} nodes found'.format(uuid, len(nodes))
        return home_with_error(error_msg)
    # Display info and charts
    try:
        chart_urls = all_chart_urls[uuid]
    except KeyError:
        chart_urls = []
    server = nodes.pop()
    return render_template('info.html', server=server, chart_urls=chart_urls)

@app.route('/start_server/<uuid>')
def start_server(uuid):
    nodes = get_nodes_by_uuid(uuid)
    if not nodes:
        error_msg = 'Cannot start server with UUID {}: Not Found'.format(uuid)
        return home_with_error(error_msg)
    if len(nodes) != 1:
        error_msg = 'Error starting server {}: {} nodes found'.format(uuid, len(nodes))
        return home_with_error(error_msg)
    node = nodes.pop()
    google_cloud_driver.ex_start_node(node)
    success_msg = 'Successfully started server {}'.format(uuid)
    return home_with_success(success_msg)

@app.route('/stop_server/<uuid>')
def stop_server(uuid):
    nodes = get_nodes_by_uuid(uuid)
    if not nodes:
        error_msg = 'Cannot stop server with UUID {}: Not Found'.format(uuid)
        return home_with_error(error_msg)
    if len(nodes) != 1:
        error_msg = 'Error stopping server {}: {} nodes found'.format(uuid, len(nodes))
        return home_with_error(error_msg)
    node = nodes.pop()
    google_cloud_driver.ex_stop_node(node)
    success_msg = 'Successfully stopped server {}'.format(uuid)
    return home_with_success(success_msg)

if __name__ == '__main__':
    app.run(debug=True)
