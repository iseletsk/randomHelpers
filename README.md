randomHelpers are a bunch of python scripts that make my life easier

## Installation
You will need credentials folder.
It should have:
- bamboohr_token.json (subdomain, api_key)
- client_secret... (google api)
- zendesk_token.json (subdomain, login, api_key)
- sendgrid_token.json (api_key, key_id, name)

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



