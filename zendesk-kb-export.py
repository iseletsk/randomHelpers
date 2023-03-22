import json

from utils_zendesk import call_zendesk
import os

WORK_DIR = 'data/zendesk-kb-export/'
os.makedirs(WORK_DIR, exist_ok=True)


def articles_to_string(articles_json, sections, skip_outdated=True, skip_draft=True,
                       skip_internal=False):
    buf = ""
    for article in articles_json['articles']:
        if sections is None or article['section_id'] in sections:
            if not skip_article(article, skip_outdated, skip_draft, skip_internal):
                buf += article_to_string(article)
    return buf


def articles_to_docs(articles_json, sections, skip_outdated=True, skip_draft=True, skip_internal=False):
    docs = []
    for article in articles_json['articles']:
        if sections is None or article['section_id'] in sections:
            if not skip_article(article, skip_outdated, skip_draft, skip_internal):
                docs.append(article_to_doc(article))
    return docs


def skip_article(article, skip_outdated=True, skip_draft=True, skip_internal=False):
    if skip_outdated and article['outdated']:
        return True
    if skip_draft and article['draft']:
        return True
    if skip_internal and article['user_segment_id'] is not None:
        return True
    return False


def article_to_doc(article):
    result = {}
    result['title'] = article['title']
    result['body'] = article['body'].replace(' ', ' ')
    result['html_url'] = article['html_url']
    result['id'] = article['id']
    result['internal'] = article['user_segment_id'] is not None
    return result

def article_to_string(article):
    buf = f'<a href="{article["html_url"]}">#{article["id"]}</a>'
    if article['body']:
        body = article['body'].replace(' ', ' ')
        buf += f'<h1>{article["title"]}</h1>\n'
        buf += f'{body}\n'
    else:
        buf += '## empty\n'
    buf += '<hr>'
    return buf


def get_articles(sections=None, loadFromFile=False, skip_outdated=True, skip_draft=True, skip_internal=False,
                 export_json_file = None):
    articles_text = ""
    page = 1
    url = 'help_center/en-us/articles.json'
    saveToFile = f'{WORK_DIR}/articles.{page}.json'
    response = call_zendesk(url, saveToFile, loadFromFile=loadFromFile)
    articles_text += articles_to_string(response, sections)
    articles_docs = []
    while response['next_page']:
        page += 1
        url = response['next_page']
        saveToFile = f'{WORK_DIR}/articles.{page}.json'
        response = call_zendesk(url, saveToFile, nextPage=True, loadFromFile=loadFromFile)
        articles_text += articles_to_string(response, sections, skip_outdated=skip_outdated, skip_draft=skip_draft,
                                            skip_internal=skip_internal)
        articles_docs += articles_to_docs(response, sections, skip_outdated=skip_outdated, skip_draft=skip_draft,
                                            skip_internal=skip_internal)

    with open(f'{WORK_DIR}/articles.html', 'w', encoding="utf-8") as f:
        f.write(f'<html><body>{articles_text}</body></html>')

    if export_json_file is not None:
        with open(export_json_file, 'w') as f_json:
            json.dump(articles_docs, f_json, indent=4, ensure_ascii=False)

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
             loadFromFile=True, skip_outdated=True, skip_draft=True, skip_internal=False,
             export_json_file='/Users/iseletsk/lve/SupportBot/workdir/articles-docs.json')

