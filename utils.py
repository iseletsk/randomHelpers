import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
def slack_connect_socket(cred_file_name):
    with open(f'credentials/{cred_file_name}', 'r') as f:
        cred = json.load(f)
        app = App(token=cred['bot_token'])
        handler = SocketModeHandler(app, cred['app_token'])
        handler.connect()
        return app, handler

