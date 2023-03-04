import requests
from bs4 import BeautifulSoup
from markdown import markdown
import re
import os

# Replace these values with your own
query = "upsert"
repo = "pinot-contrib/pinot-docs"
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
def search_github_documentation(query_items):
    doc_url_list = []
    for query in query_items:
        url = f"https://api.github.com/search/code?q={query}+repo:{repo}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            results = response.json()["items"]
            for result in results:
                filename = result["name"]
                file_url = result["url"]
                html_url = result["html_url"]
                if not html_url.endswith(".md"):
                    continue
                file_url_response = requests.get(file_url)
                if file_url_response.status_code == 200:
                    download_url = file_url_response.json()["download_url"]
                    print(f"{filename}: {download_url}")
                    doc_url_list.append(download_url)
                    if len(doc_url_list) > MAX_URL_COUNT:
                        break
                else:
                    print(f"Error searching File URL {file_url} GitHub: {response.status_code}")

        else:
            print(f"Error searching GitHub: {response.status_code}")
    return doc_url_list
