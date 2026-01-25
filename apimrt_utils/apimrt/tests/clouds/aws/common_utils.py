import json
from os import path


def get_test_folder_path():
    return path.dirname(path.abspath(__file__))


def get_mock_json(data):
    with open(path.join(get_test_folder_path(), 'mock_data', '{data}.json'.format(data=data)), 'r') as oauth_resp:
        return json.loads(oauth_resp.read())


def get_mock_data(data):
    with open(path.join(get_test_folder_path(), 'mock_data', '{data}'.format(data=data)), 'r') as oauth_resp:
        return oauth_resp.read()
    