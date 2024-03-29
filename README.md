randomHelpers are a bunch of python scripts that make my life easier

## Installation
You will need credentials folder.
It should have:
- bamboohr_token.json (subdomain, api_key)
- client_secret... (google api)
- zendesk_token.json (subdomain, login, api_key)
- sendgrid_token.json (api_key, key_id, name)
- slack_monthly_token.json (app_token, bot_token)

## zendesk_to_pdf.py 
This script takes a list of categories & zendesk tasks from the gDrive, 
downloads tickets from zendesk, formats them into bunch of HTMLs + index.html, zips them, uploads them to gDrive.
It also can convert those HTML files into PDFs. The idea is to simplify reading.



```
config_dir/zendesk_to_pdf.yaml - config params
zendesk_to_pdf_requirements.txt - python requirements
```

support tags/categories should look be on gdrive in text file looking like this:
```
IF (INCLUDES_ALL([Ticket tags], "clos_kernel","kernel_general","product_question")) THEN "Question about kernel"
ELIF (INCLUDES_ALL([Ticket tags], "clos_kernel","kernel_module","product_question")) THEN "Question about kernel module"
ELIF (INCLUDES_ALL([Ticket tags], "clos_kernel","kernel_issue","product_question")) THEN "Question about kernel issue"
ELIF (INCLUDES_ALL([Ticket tags], "clos_kernel","kernel_boot","product_question")) THEN "Question about kernel boot"
```
Once uploaded notification is sent to slack channel zendesk-monthly-export


## client_categorization.py
The script retrieves bunch of companies from hubspot (based on a particular list), 
retrieves the website related to the domain, and marks it as Hosting in company_type property (based on gpt-3.5 classification) if it is hosting
In either case it sets company_type_tested to True

It requires openai & hubspot api keys
hubspot_token.json (api_key)
openai_token.json (api_key)

uses free_emails.txt to track free email services

```