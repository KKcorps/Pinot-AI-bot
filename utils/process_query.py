# import nltk
from nltk.corpus import stopwords
import string
import argparse

from utils.github_helper import search_github_documentation, get_doc_content
from utils.openai_helper import generate_response

import sys


## return list of search terms : list[str]
def get_search_terms(query):
    # Tokenize the question
    tokens = nltk.word_tokenize(query)

    # Remove stop words
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [word for word in tokens if not word.lower() in stop_words]

    # Remove punctuations
    punctuations = set(string.punctuation)
    filtered_tokens = [word for word in filtered_tokens if not word in punctuations]
    
    # print("FILTERED TOKENS:\n")
    # print(filtered_tokens)
    return list(set(filtered_tokens))


def generate_response(query):
    print(f"Question Asked by the user: {query}")

    search_terms = get_search_terms(query)
    documentation_urls = search_github_documentation([query])
    if len(documentation_urls) == 0:
        documentation_urls = search_github_documentation([','.join(search_terms)])
    
    if len(documentation_urls) == 0:
        print("Sorry couldn't find anything! Give it another try with a modified question!")
        return "Sorry couldn't find anything! Give it another try with a modified question!"
    for url in documentation_urls:
        doc_text = get_doc_content(url)
        ai_output = generate_response(doc_text, query)
        print(f"Here's what Pinot AI bot thinks you should do:\n {ai_output}")
        print("Hope, you're satisfied trin trin")
        return ai_output

if __name__ == "__main__":
    # nltk.download('punkt')
    # nltk.download('stopwords')

    parser = argparse.ArgumentParser(
                    prog = 'PinotAIBot',
                    description = 'Answer your common Pinot Queries')
    parser.add_argument('-q', '--query')
    parser.add_argument('-v', '--verbose')
    args = parser.parse_args()

    query = args.query
    if query is None:
        print("No query provided!")
        sys.exit(-1)
    
    generate_response(query)

    

