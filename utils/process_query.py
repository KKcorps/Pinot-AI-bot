from nltk import word_tokenize, pos_tag
from nltk.corpus import stopwords
import string
import argparse

from utils.github_helper import search_github_documentation, get_doc_content
from utils.openai_helper import ask_gpt_using_summaries
from utils.pinecone_helper import query_index

import re
import sys
from dotenv import load_dotenv
load_dotenv(override=True)

def format_text(text):
    text = re.sub(r'\n+', '\n', text)
    return text

## return list of search terms : list[str]
def get_search_terms(query):
    # Tokenize the question
    tokens = word_tokenize(query)

    tagged_tokens = pos_tag(tokens)
    search_tokens = [word for word, pos in tagged_tokens if pos in ['NN', 'NNS', 'NNP', 'JJ']]
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [word for word in search_tokens if not word.lower() in stop_words]

    # Remove punctuations
    punctuations = set(string.punctuation)
    filtered_tokens = [word for word in filtered_tokens if not word in punctuations]
    

    return list(set(filtered_tokens))


def generate_response(query):
    print(f"Question Asked by the user: {query}")

    documentation_urls = query_index(query)
    
    # documentation_urls = search_github_documentation([query])
    if len(documentation_urls) == 0:
        search_terms = get_search_terms(query)
        documentation_urls = search_github_documentation(['+'.join(search_terms)])
    
    if len(documentation_urls) == 0:
        print("Sorry couldn't find anything! Give it another try with a modified question!")
        return "Sorry couldn't find anything! Give it another try with a modified question!"
    for url in documentation_urls:
        doc_text = get_doc_content(url[0])
        # ai_output = ask_gpt(doc_text, query)
        ai_output = ask_gpt_using_summaries(doc_text, query)
        formatted_output = f"{format_text(ai_output)} \n\n For more you can checkout the following documentation: {str(url[1])}"
        print(f"Here's what Pinot AI bot thinks you should do:\n {formatted_output}")
        return formatted_output

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
    # print(get_search_terms(query))

    


