import html
import os
from datetime import datetime
from dateutils import relativedelta

import requests
from requests.auth import HTTPBasicAuth
import json
from string import Template

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
import random

import argparse
import yaml

ENCODING = 'UTF-8'

SCOPES = ['https://www.googleapis.com/auth/drive']

CONFIG_DIR = 'config_dir'


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



def get_zendesk_ticket(ticket_id, loadFromFile = False):
    ticket = call_zendesk(f'tickets/{ticket_id}.json', saveToFile=f'{JSON_DIR}ticket.{ticket_id}.json', loadFromFile=loadFromFile)
    comments = call_zendesk(f'tickets/{ticket_id}/comments.json', saveToFile=f'{JSON_DIR}comment.{ticket_id}.json', loadFromFile=loadFromFile)
    return ticket, comments

def get_zendesk_users(ticket_id, user_ids, loadFromFile = False):
    return call_zendesk(f'users/show_many.json?ids={",".join(user_ids)}', saveToFile=f'{JSON_DIR}users.{ticket_id}.json', loadFromFile=loadFromFile)

def load_ticket(ticket_id):
    with open(f'{JSON_DIR}ticket.{ticket_id}.json') as f:
        ticket = json.load(f)
    with open(f'{JSON_DIR}comment.{ticket_id}.json') as f:
        comments = json.load(f)
    return ticket, comments

def load_users(ticket_id):
    with open(f'{JSON_DIR}users.{ticket_id}.json') as f:
        users_json = json.load(f)
        return users_json['users']


STYLE = """
<style>
@media print {
  .new-page {
    page-break-before: always;
  }
}
.public {background-color: white;}
.comment-private {background-color: burlywood;}
.comment-user {background-color: white;}
.comment-agent {background-color: cornsilk;}
.first-comment {background-color: lightblue; display: none;}
.first-comment-button { cursor:pointer; text-decoration: underline; }

.zd-comment {border-style: outset;}
hr {
    display: block;width: 20%;
    align: left;}
.signature {border-style: dashed; display: none; }
.user-agent {weight: italic; color: blue; display: inline;}
.user-admin {weight: italic; color: red; display: inline;}
.user-end-user {weight: bold; color: green; display: inline;}
</style>
"""

TICKET_TEMPLATE = """
<a name="$ticket_id"><h2># $ticket_id | $subject </h2></a>
"""

COMMENT_TEMPLATE="""
<div class="$comment_type"><div class="user-$role">$name</div>
<i> [$created]</i><br>
$html_body
</div>
"""

AUTHORS = {}

def init_authors(ticket_id, comments, loadFromFile = False):
    author_ids = set()
    for comment in comments['comments']:
        author_id = str(comment['author_id'])
        if author_id not in AUTHORS:
            author_ids.add(author_id)
    if author_ids:
        users_json = get_zendesk_users(ticket_id, author_ids, loadFromFile=loadFromFile)
        for user in users_json['users']:
            AUTHORS[str(user['id'])] = user

def ticket_to_html_code(ticket_id, loadFromFile = False):
    code = ""
    ticket, comments = get_zendesk_ticket(ticket_id, loadFromFile=loadFromFile)
    init_authors(ticket_id, comments, loadFromFile=loadFromFile)
    s = Template(TICKET_TEMPLATE)
    code += s.substitute(ticket_id=ticket_id, subject=ticket['ticket']['subject'])
    s = Template(COMMENT_TEMPLATE)
    for comment in comments['comments']:
        comment_type='comment-private'
        user = AUTHORS[str(comment['author_id'])]
        if comment['public']:
            if user['role'] == 'end-user':
                comment_type='comment-user'
            else:
                comment_type='comment-agent'
        code += s.substitute(comment_type=comment_type,
                             role=user['role'],
                             name=user['name'],
                             created=comment['created_at'],
                             html_body=comment['html_body'])
    return code

def ticket_to_html(ticket_id):
    with open(f'{RESULTS_DIR}/ticket.{ticket_id}.html', 'wb') as f:
        f.write(f'<html><head>{STYLE}</head><body>\n'.encode(ENCODING))
        f.write(ticket_to_html_code(ticket_id).encode(ENCODING))
        f.write('</body></html>'.encode(ENCODING))

HTML_EXTENSION = '.html'
def ticket_category_to_html(category_name, ticket_list, loadFromFile = False):
    html_file_name = f'{category_name}{FILE_SUFFIX}'
    toc = "<h2>Table of Contents</h2>\n<ul>\n"
    #            f'<button type="button" id="fc-{ticket_id}" class="first-comment-button">toggle first comment</button>\n' \

    for ticket_id in ticket_list:
        ticket, comments = get_zendesk_ticket(ticket_id, loadFromFile=loadFromFile)
        first_comment = comments['comments'][0]
        toc += f'<li><a href="#{ticket_id}">{ticket_id} | {ticket["ticket"]["subject"]}</a>' \
                f' <a id="fc-{ticket_id}" class="first-comment-button"> ... </a>'\
               f'<div id="fc-{ticket_id}-div" class="first-comment">{first_comment["html_body"][:2500]} ...</div>' \
               f'</li>\n'
    toc += "</ul>\n"
    toc += """<script>
var elements = document.getElementsByClassName("first-comment-button");
for (var i = 0; i < elements.length; i++) {
    elements[i].addEventListener("click", function() {
        var el = document.getElementById(this.id+"-div");
        if (el.style.display === "block") {
            el.style.display = "none";
        } else {
            el.style.display = "block";
        }
    })
}; 
</script>  
"""

    with open(f'{RESULTS_DIR}/{html_file_name}{HTML_EXTENSION}', 'wb') as f:
        f.write(f'<html><head>{STYLE}</head><body>\n'.encode(ENCODING))
        f.write(f'<h1>{category_name}</h1>\n'.encode(ENCODING))
        today = datetime.now().strftime("%Y-%m-%d")
        f.write(f'<div>{len(ticket_list)} tickets, generated on {today}</div>\n'.encode(ENCODING))
        f.write(toc.encode(ENCODING))
        for ticket_id in ticket_list:
            f.write(ticket_to_html_code(ticket_id, loadFromFile=True).encode(ENCODING))
            f.write('<hr>\n'.encode(ENCODING))
        f.write('</body></html>'.encode(ENCODING))
    print("Generated HTML", category_name)
    return html_file_name

def html_to_pdf(file_name):
    # options = {
    #     'encoding': ENCODING,
    # }
    print("Generating PDF", file_name)
    from weasyprint import HTML
    html = HTML(f'{RESULTS_DIR}/{file_name}{HTML_EXTENSION}')
    html.write_pdf(f'{RESULTS_DIR}/{file_name}.pdf')


def ticket_to_pdf(ticket_id):
    ticket_to_html(ticket_id)
    # options = {
    #     'encoding': ENCODING,
    # }
    from weasyprint import HTML
    html = HTML(f'{RESULTS_DIR}/{ticket_id}.html')
    html.write_pdf(f'{RESULTS_DIR}/{ticket_id}.pdf')


def zendesk_ticket_to_pdf(ticket_id):
    get_zendesk_ticket(ticket_id)
    ticket_to_html(ticket_id)
    ticket_to_pdf(ticket_id)


def zendesk_tickets_by_tag(tag, created_after, loadFromFile = False):
    tickets_json = call_zendesk(f'search/export.json?query=tags:{tag} created>{created_after} type:ticket',
                                saveToFile=f'{JSON_DIR}tickets.{tag}.json', loadFromFile=loadFromFile)
    return tickets_json_to_list(tickets_json)


def zendesk_tickets_updated_after(after_date, loadFromFile = False):
    page = 1
    tickets_json = call_zendesk(f'search/export.json?query=updated>{after_date}&filter[type]=ticket&page[size]=1000',
                                saveToFile=f'{JSON_DIR}tickets.updated.{after_date}.{page}.json', loadFromFile=loadFromFile)
    while tickets_json['meta']['has_more']:
        page += 1
        print(f'page {page}')
        tickets_json = call_zendesk(tickets_json['links']['next'],
                                    saveToFile=f'{JSON_DIR}tickets.updated.{after_date}.{page}.json',
                                    nextPage=True, loadFromFile=loadFromFile)
    return load_tickets_updated_after(after_date)

def load_tickets_updated_after(after_date):
    tickets = []
    page = 1
    while True:
        try:
            with open(f'{JSON_DIR}tickets.updated.{after_date}.{page}.json', 'r') as f:
                tickets_json = json.load(f)
                for ticket in tickets_json['results']:
                    if ticket['tags']:
                        tickets.append((ticket["id"], ticket['tags']))
                page += 1
        except FileNotFoundError:
            break
    return tickets

def tickets_json_to_list(tickets_json):
    ticket_list = []
    for ticket in tickets_json['results']:
        ticket_list.append(ticket['id'])
    return ticket_list

def load_tickets_by_tag(tag, created_after):
    with open(f'{JSON_DIR}tickets.{tag}.json', 'r') as f:
        tickets_json = json.load(f)
        return tickets_json_to_list(tickets_json)


# get_zendesk_ticket(168411)
# ticket, comments = load_ticket(168411)
#ticket_to_html(168411)
#ticket_to_pdf(168411)

# zendesk_ticket_to_pdf(160899)
# zendesk_ticket_to_pdf(162133)
# zendesk_ticket_to_pdf(162180)

## ticket_category_to_pdf('Question about ALT-PHP Version', [159763, 161697, 162525, 163980, 164702, 165251])

## getting tickets to PDF using tags
# tag = "alt-php_version"
# topic = "Question about ALT-PHP Version"
# created_after = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
# ticket_category_to_pdf(topic, zendesk_tickets_by_tag(tag, created_after))
#
#
#
# ticket_json = load_tickets_by_tag(tag, created_after)
# https://pypi.org/project/pdfkit/

def parse_tags_and_names(filename):
    """Parse into tags & name from the file with this format
    IF (INCLUDES_ALL([Ticket tags], "clos_kernel","kernel_general","product_question")) THEN "Question about kernel"
    ELIF (INCLUDES_ALL([Ticket tags], "clos_kernel","kernel_module","product_question")) THEN "Question about kernel module"
    ELIF (INCLUDES_ALL([Ticket tags], "clos_kernel","kernel_issue","product_question")) THEN "Question about kernel issue
"""
    tags = []
    names = []
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith('ELIF') or line.startswith('IF'):
                line = line.replace('ELIF (INCLUDES_ALL([Ticket tags], ', '')
                line = line.replace('IF (INCLUDES_ALL([Ticket tags], ', '')
                x, y = line.split('THEN', 2)
                x = x.replace('"', '').replace(')', '').strip()
                tags.append(x.split(','))
                names.append(y.strip().strip('"'))
    return tags, names



def export_tickets_by_tag_category(from_date, pdf_export=False, loadFromFile=False):
    tags, names = parse_tags_and_names(SUPPORT_TAGS)
    print(len(tags), len(names))
    tickets = zendesk_tickets_updated_after(from_date, loadFromFile=loadFromFile)
    print(len(tickets))
    print(tickets[0])

    ticket_categories = {}
    count = 0
    for ticket_id, ticket_tags in tickets:
        count += 1
        for tag, name in zip(tags, names):
            if set(tag).issubset(ticket_tags):
                if name not in ticket_categories:
                    ticket_categories[name] = []
                ticket_categories[name].append(ticket_id)

    html_index_body = f'<html><body><h1>Zendesk tickets {from_date}</h1><ul>'
    results = {k: v for k, v in sorted(ticket_categories.items(), key=lambda item: len(item[1]), reverse=True)}
    import zipfile
    with zipfile.ZipFile(f'{RESULTS_DIR}/zendesk_tickets_{from_date}.zip', 'w') as myzip:
        for category_name, ticket_ids in results.items():
            if len(ticket_ids) >= 10:
                if category_name.endswith(' (?)'):
                    category_name = category_name[:-4]
                category_name = category_name.replace('/', ' and ')
                print(category_name, len(ticket_ids))
                filename = ticket_category_to_html(category_name, ticket_ids, loadFromFile=True)
                html_index_body += f'<li><a href="{filename}{HTML_EXTENSION}">{category_name} ({len(ticket_ids)})</a></li>'
                myzip.write(f'{RESULTS_DIR}/{filename}{HTML_EXTENSION}', arcname=f'{from_date}/{filename}{HTML_EXTENSION}')
                if pdf_export:
                    html_to_pdf(filename)
        html_index_body += '</ul></body></html>'
        with open(f'{RESULTS_DIR}/index.html', 'w') as f:
            f.write(html_index_body)
        myzip.write(f'{RESULTS_DIR}/index.html', arcname=f'{from_date}/index.html')



def get_start_date(now, days_ago=0, months_ago=0):
    return (now - relativedelta(months=months_ago, days=days_ago)).strftime("%Y-%m-%d")



def gdrive_login():
    credentials = None
    try:
        if os.path.exists(GDRIVE_CRED_FILE):
            with open(GDRIVE_CRED_FILE, 'rb') as token:
                credentials = pickle.load(token)
                drive_service = build('drive', 'v3', credentials=credentials)  # lets see if it works
    except Exception as e:
        print(e)
        credentials = None

    if credentials is None:
        flow = InstalledAppFlow.from_client_secrets_file(GDRIVE_SECRET, SCOPES)
        credentials = flow.run_local_server(host='127.0.0.1',
                                            port=8080 + random.randrange(0, 100),
                                            authorization_prompt_message='Please visit this URL: {url}',
                                            success_message='The auth flow is complete; you may close this window.',
                                            open_browser=True)
        with open(GDRIVE_CRED_FILE, 'wb') as token:
            pickle.dump(credentials, token)

    drive_service = build('drive', 'v3', credentials=credentials)
    # docs_service = build('docs', 'v1', credentials=credentials)
    return drive_service


def download_from_gdrive(drive_service, file_id, filename):
    resp = drive_service.files().get_media(fileId=file_id).execute()
    with open(filename, "wb") as f:
        f.write(resp)


def create_folder_gdrive(drive_service, folder_name, parent_folder_id):
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder_id],
    }
    file = drive_service.files().create(supportsTeamDrives=True, body=file_metadata,
                                        fields='id').execute()
    return file.get('id')

def upload_to_gdrive(drive_service, filename, folder_id, path_to_file):
    file_metadata = {
        'name': filename,
        'description': filename,
        'parents': [folder_id],
    }
    media = MediaFileUpload(path_to_file, mimetype='application/pdf', resumable=True)
    file = drive_service.files().create(supportsTeamDrives=True, body=file_metadata, media_body=media, fields='id').execute()
    print(F'File with ID: "{file.get("id")}" has been uploaded.')
    print(F'https://drive.google.com/file/d/{file.get("id")}/view?usp=sharing')
    print('File ID: %s' % file.get('id'))


SUPPORT_TICKETS_EXPORT_FOLDER = ''
TAG_FILE_ID = ""
SUPPORT_TAGS = ""
GDRIVE_SECRET = ""
GDRIVE_CRED_FILE = ""

WORK_DIR = 'data'
JSON_DIR = 'data/json'
RESULTS_DIR = 'data/pdf'
FILE_SUFFIX = ""

def init_from_yaml():
    with open(f'{CONFIG_DIR}/zendesk_to_pdf.yaml', 'r') as f:
        config = yaml.safe_load(f)
    global TAG_FILE_ID
    global SUPPORT_TICKETS_EXPORT_FOLDER
    global GDRIVE_SECRET
    global GDRIVE_CRED_FILE

    TAG_FILE_ID = config['gdrive']['tag-file-id']
    SUPPORT_TICKETS_EXPORT_FOLDER = config['gdrive']['dest-folder-id']
    GDRIVE_SECRET = config['gdrive']['secret-file']
    GDRIVE_CRED_FILE = config['gdrive']['cred-file']

def init_dirs(from_date):
    global WORK_DIR
    global JSON_DIR
    global RESULTS_DIR
    global FILE_SUFFIX
    global SUPPORT_TAGS
    WORK_DIR = os.path.join(WORK_DIR, from_date) + "/"
    JSON_DIR = os.path.join(WORK_DIR, 'json') + "/"
    RESULTS_DIR = os.path.join(WORK_DIR, 'results') + "/"
    os.makedirs(JSON_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    FILE_SUFFIX = "-"+from_date
    SUPPORT_TAGS = os.path.join(WORK_DIR, 'support-tags.txt')


def upload_pdf_to_gdrive(from_dir, target_folder, drive_service):
    for file in os.listdir(from_dir):
        if file.endswith(".pdf"):
            upload_to_gdrive(drive_service, file, target_folder, from_dir + file)


def recurrent_export(now, days_ago, months_ago, pdf_export=False, gdrive_upload=True):
    from_date = get_start_date(now, days_ago=days_ago, months_ago=months_ago)
    today = now.strftime("%Y-%m-%d")
    init_dirs(today)
    init_from_yaml()
    drive_service = gdrive_login()
    download_from_gdrive(drive_service, TAG_FILE_ID, SUPPORT_TAGS)

    export_tickets_by_tag_category(from_date, loadFromFile=True, pdf_export=pdf_export)

    if gdrive_upload:
        target_folder_id = create_folder_gdrive(drive_service, today, SUPPORT_TICKETS_EXPORT_FOLDER)
        if pdf_export:
            upload_pdf_to_gdrive(RESULTS_DIR, target_folder_id, drive_service)

        if gdrive_upload:
            upload_to_gdrive(drive_service, f'zendesk_tickets_{from_date}-{today}.zip', target_folder_id, f'{RESULTS_DIR}/zendesk_tickets_{from_date}.zip')

if __name__ == '__main__':
    main_parser = argparse.ArgumentParser(description='Export support tickets to PDFs')
    main_parser.add_argument('--export-category', action='store_true', help='Export tickets by category')
    main_parser.add_argument('--today', type=str, help='Consider today to be this date, in %Y-%m-%d format')
    main_parser.add_argument('--auth', action='store_true', help='Do Google Drive authentication')
    main_parser.add_argument('--days', type=int, default=0, help='Number of days to go back')
    main_parser.add_argument('--months', type=int, default=1, help='Number of months to go back')
    main_parser.add_argument('--pdf-export', action='store_true', help='Export tickets to PDF')
    main_parser.add_argument('--gdrive-upload', action='store_true', help='Export all tickets')

    args = main_parser.parse_args()
    if args.export_category:
        now = datetime.now()
        if args.today:
            now = datetime.strptime(args.today, "%Y-%m-%d")
        recurrent_export(now, args.days, args.months, args.pdf_export, args.gdrive_upload)
    if args.auth:
        init_from_yaml()
        init_dirs(datetime.now().strftime("%Y-%m-%d"))
        gdrive_login()
