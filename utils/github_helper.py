import requests
from bs4 import BeautifulSoup
from markdown import markdown
import re
import os

from dotenv import load_dotenv
load_dotenv(override=True)

# Replace these values with your own
DOCUMENTATION_REPOSITORY_LIST = os.environ.get('GITHUB_REPO_LIST', 'pinot-contrib/pinot-docs').split(":")
MAX_URL_COUNT = 1
GITHUB_SEARCH_API = "https://api.github.com/search/code"

token = os.environ["GITHUB_API_KEY"]

headers = {"Authorization": f"Bearer {token}"}

def count_code_blocks(markdown_text):
    # Define a regular expression to match code blocks
    code_regex = re.compile(r"```(?:\w+)?\n([\s\S]*?)\n```")

    # Find all matches of code blocks in the text
    matches = code_regex.finditer(markdown_text)

    # Extract the code blocks along with their start indices
    code_blocks = [(match.start(), match.group(1)) for match in matches]

    return len(code_blocks)

## return block of text from the doc: str
def get_doc_content(file_url):
    response = requests.get(file_url, headers=headers)
    markdown_content = response.text
    cleaner_text_content = re.sub(r'\n+', '\n', markdown_content) 
    content = cleaner_text_content.strip()
    return (content, count_code_blocks(content), file_url)


## return list of tuples containing (raw_markdown_file_url, github_file_url, html_file_url)
def search_github_documentation(query_items):
    doc_url_list = set()
    file_url_list = set()
    for repo in DOCUMENTATION_REPOSITORY_LIST:
        print(f"Searching in repo: {repo}")
        for query in query_items:
            if len(doc_url_list) >= MAX_URL_COUNT:
                break
            url = f"{GITHUB_SEARCH_API}?q={query}+repo:{repo}+extension:md"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                results = response.json()["items"]
                for result in results:
                    filename = result["name"]
                    file_url = result["url"]
                    html_url = result["html_url"]
                    if not html_url.endswith(".md"):
                        continue
                    if "/releases/" in html_url or "release-notes" in html_url:
                        continue
                    if file_url in file_url_list:
                        continue
                    file_url_list.add(file_url)
                    file_url_response = requests.get(file_url, headers=headers)
                    if file_url_response.status_code == 200:
                        download_url = file_url_response.json()["download_url"]
                        url_tuple = (download_url, html_url)
                        if url_tuple not in doc_url_list:
                            print(f"{filename}: {url_tuple}")
                            doc_url_list.add(url_tuple)
                            if len(doc_url_list) >= MAX_URL_COUNT:
                                break
                    else:
                        print(f"Error searching File URL {file_url} GitHub: {response.status_code}")

            else:
                print(f"Error searching GitHub: {response.status_code}")
    return list(doc_url_list)