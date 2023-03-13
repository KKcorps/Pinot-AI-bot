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
    # Define a regular expression pattern to match lines starting with "Documentation:" and containing hyperlinks
    pattern = r"^Documentation:.*https?://\S+.*$"
    # Use re.sub() to replace lines matching the pattern with an empty string
    new_text = re.sub(pattern, "", text, flags=re.MULTILINE)

    pattern = r"For more information.*https?://\S+.*$"
    # Use re.sub() to replace lines matching the pattern with an empty string
    new_text = re.sub(pattern, "", new_text, flags=re.MULTILINE)

    pattern = r"refer to.*https?://\S+.*$"
    # Use re.sub() to replace lines matching the pattern with an empty string
    new_text = re.sub(pattern, "", new_text, flags=re.MULTILINE)

    return new_text

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

def format_response(output, url):
    formatted_output = f"\n{format_text(output)} \n\nFor more you can checkout the following documentation: {str(url)}"
    print(f"Here's what Pinot AI bot thinks you should do:\n {formatted_output[:100]}...{len(formatted_output) - 100} more characters")
    return formatted_output    

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
    
    content_list = []
    for url in documentation_urls:
        print(f"Fetching content for: {url[1]}")
        content_list.append(get_doc_content(url[0]))

    #TODO: Maybe I can index the count of code blocks in pinecone metadata itself??
    for doc in content_list:
        doc_text = doc[0]
        code_blocks_len = doc[1]
        #This is a hack to give priority to docs containing configuration examples
        if (code_blocks_len == 0):
            continue
        else:
            print(f"Asking AI using doc: {doc[2]} with {code_blocks_len} code blocks")
            (ai_output, code_blocks) = ask_gpt_using_summaries(doc_text, query)
            return format_response(ai_output, doc[2])
    
    print(f"Asking AI using doc: {content_list[0][2]} with {content_list[0][2]} code blocks")
    (ai_output, code_blocks) = ask_gpt_using_summaries(content_list[0][0], query)
    return format_response(ai_output, content_list[0][2])

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

    


