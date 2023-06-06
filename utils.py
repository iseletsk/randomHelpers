import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import yaml
def slack_connect_socket(cred_file_name):
    with open(f'credentials/{cred_file_name}', 'r') as f:
        cred = json.load(f)
        app = App(token=cred['bot_token'])
        handler = SocketModeHandler(app, cred['app_token'])
        handler.connect()
        return app, handler

def load_openai_creds():
    with open('credentials/openai.json', 'r') as f:
        creds = json.load(f)
        import os
        import openai
        openai.api_key = creds['openai_api_key']
        os.environ["OPENAI_API_KEY"] = creds['openai_api_key']
        return creds

def load_hubspot_creds():
    with open('credentials/hubspot_token.json', 'r') as f:
        creds = json.load(f)
        return creds['api_key']


def load_google_creds():
    from oauth2client.service_account import ServiceAccountCredentials

    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials/driveautomation-354723-abc919c39f3b.json', scope)
    return credentials


def load_dilisense_creds():
    with open('credentials/dilisense.json', 'r') as f:
        creds = json.load(f)
        return creds


def load_payroll_config():
    with open('config_dir/payroll_config.yaml', 'r') as f:
        conf = yaml.safe_load(f)
        return conf


def column_id_to_name(index):
    column_name = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        column_name = chr(65 + remainder) + column_name
    return column_name
