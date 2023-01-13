from utils_zendesk import call_zendesk
import os

WORK_DIR = 'data/zendesk-kb-export/'
os.makedirs(WORK_DIR, exist_ok=True)


def articles_to_string(articles_json, sections, skip_outdated=True, skip_draft=True):
    buf = ""
    for article in articles_json['articles']:
        if sections is None or article['section_id'] in sections:
            buf += article_to_string(article, skip_outdated, skip_draft)
    return buf


def article_to_string(article, skip_outdated=True, skip_draft=True):
    if skip_outdated and article['outdated']:
        return ""
    if skip_draft and article['draft']:
        return ""

    buf = f'<a href="{article["html_url"]}">#{article["id"]}</a>'
    if article['body']:
        body = article['body'].replace(' ', ' ')
        buf += f'<h1>{article["title"]}</h1>\n'
        buf += f'{body}\n'
    else:
        buf += '## empty\n'
    buf += '<hr>'
    return buf


def get_articles(sections=None, loadFromFile=False):
    articles_text = ""
    page = 1
    url = 'help_center/en-us/articles.json'
    saveToFile = f'{WORK_DIR}/articles.{page}.json'
    response = call_zendesk(url, saveToFile, loadFromFile=loadFromFile)
    articles_text += articles_to_string(response, sections)
    while response['next_page']:
        page += 1
        url = response['next_page']
        saveToFile = f'{WORK_DIR}/articles.{page}.json'
        response = call_zendesk(url, saveToFile, nextPage=True, loadFromFile=loadFromFile)
        articles_text += articles_to_string(response, sections)

    with open(f'{WORK_DIR}/articles.html', 'w', encoding="utf-8") as f:
        f.write(f'<html><body>{articles_text}</body></html>')


cl_sections = [
    360004078100,
    360003982120,
    115001538929,
    360004068620,
    360004068600,
    360004068660,
    360004074740,
    360004115739,
    360004074720,
    360004068640,
    360004103500,
    360004080940,
    360004103260
]
get_articles(sections=cl_sections,
             loadFromFile=True)
