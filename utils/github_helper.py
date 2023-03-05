import requests
from bs4 import BeautifulSoup
from markdown import markdown
import re
import os

# Replace these values with your own
query = "upsert"
documention_repo = "pinot-contrib/pinot-docs"
code_repo = "apache/pinot"

token = os.environ["GITHUB_API_KEY"]


headers = {"Authorization": f"Bearer {token}"}
MAX_URL_COUNT = 1

## return block of text from the doc: str
def get_doc_content(file_url):
    response = requests.get(file_url)
    markdown_content = response.text
    # Convert the Markdown content to HTML
    # html_content = markdown(markdown_content)
    # text_content = ''.join(BeautifulSoup(html_content).findAll(text=True))
    cleaner_text_content = re.sub(r'\n+', '\n', markdown_content) 
    # print("CLEAN TEXT: " + cleaner_text_content.strip()[:100])
    return cleaner_text_content.strip()


## return list of urls:  ['https://file1.md']
def search_configs_in_repo(query_items):
    doc_url_list = set()
    file_url_list = set()
    for query in query_items:
        url = f"https://api.github.com/search/code?q={query}+repo:{code_repo}+extension:json+extension:yaml+extension:properties"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            results = response.json()["items"]
            for result in results:
                filename = result["name"]
                file_url = result["url"]
                html_url = result["html_url"]
                if not html_url.endswith(".md"):
                    continue
                if file_url in file_url_list:
                    continue
                file_url_list.add(file_url)
                file_url_response = requests.get(file_url)
                if file_url_response.status_code == 200:
                    download_url = file_url_response.json()["download_url"]
                    if download_url not in doc_url_list:
                        print(f"{filename}: {download_url}")
                        doc_url_list.add(download_url)
                        if len(doc_url_list) > MAX_URL_COUNT:
                            break
                else:
                    print(f"Error searching File URL {file_url} GitHub: {response.status_code}")

        else:
            print(f"Error searching GitHub: {response.status_code}")
    return list(doc_url_list)

## return list of urls:  ['https://file1.md']
def search_github_documentation(query_items):
    doc_url_list = set()
    file_url_list = set()
    for query in query_items:
        if len(doc_url_list) >= MAX_URL_COUNT:
            break
        url = f"https://api.github.com/search/code?q={query}+repo:{documention_repo}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            results = response.json()["items"]
            for result in results:
                filename = result["name"]
                file_url = result["url"]
                html_url = result["html_url"]
                if not html_url.endswith(".md"):
                    continue
                if file_url in file_url_list:
                    continue
                file_url_list.add(file_url)
                file_url_response = requests.get(file_url)
                if file_url_response.status_code == 200:
                    download_url = file_url_response.json()["download_url"]
                    if download_url not in doc_url_list:
                        print(f"{filename}: {download_url}")
                        doc_url_list.add(download_url)
                        if len(doc_url_list) >= MAX_URL_COUNT:
                            break
                else:
                    print(f"Error searching File URL {file_url} GitHub: {response.status_code}")

        else:
            print(f"Error searching GitHub: {response.status_code}")
    return list(doc_url_list)