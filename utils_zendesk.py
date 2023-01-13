import json
import os

import requests
from requests.auth import HTTPBasicAuth


def call_zendesk(url, saveToFile = None, nextPage = False, loadFromFile = False):
    if loadFromFile & os.path.exists(saveToFile):
        with open(saveToFile) as f:
            return json.load(f)
    print(f'Calling {url}, cannot find file {saveToFile}')
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    with open('credentials/zendesk_token.json') as f:
        zendesk_credentials = json.load(f)
        subdomain = zendesk_credentials['subdomain']
        login = zendesk_credentials['login']+"/token"
        api_key = zendesk_credentials['api_key']

        if not nextPage:
            url = f'https://{subdomain}.zendesk.com/api/v2/{url}'

        r = requests.get(url, auth=HTTPBasicAuth(login, api_key), headers=headers)

        if r.status_code != 200:
            raise Exception(f'Unable to get url {url} - {r.status_code}')
        if saveToFile:
            with open(saveToFile, 'w') as f:
                json.dump(r.json(), f, indent=2)
        return r.json()
