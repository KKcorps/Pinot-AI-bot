import openai
import os
from dotenv import load_dotenv

import tiktoken

load_dotenv(override=True)

openai.api_key = os.environ["OPEN_AI_KEY"]
MAX_DOC_LENGTH = 2048
CHUNK_LENGTH = 2048
CHUNK_OVERLAP_LENGTH = 128
RESPONSE_TOKEN_MAX = 2048
CHUNK_SUMMARY_LENGTH = 512
MODEL_ENGINE = "gpt-3.5-turbo"
MODEL_TEMPERATURE = 0.2
FREQUENCY_PENALTY = 1.0
PRESENCE_PENALTY = 1.0


config_prompt = "A Configuration is any text that starts with ``` and ends with ```. If there is a word after ``` that is generally considered as format. e.g. ```json  {   'enableSnapshot' : true } is a config in json format with keys as `enableSnapshot` and value as `true`. If a config is present, add it to the response in the format `Configuration`: followed by a configuration example."

#TODO: Implement a summarise function that can be used after multiple calls

encoding = tiktoken.encoding_for_model(MODEL_ENGINE)

def count_tokens(text):
    input_ids = encoding.encode(text)
    num_tokens = len(input_ids)
    return num_tokens

def break_up_text_to_chunks(text, chunk_size=CHUNK_LENGTH, overlap=CHUNK_OVERLAP_LENGTH):
    tokens = encoding.encode(text)
    num_tokens = len(tokens)
    
    chunks = []
    for i in range(0, num_tokens, chunk_size - overlap):
        chunk = tokens[i:i + chunk_size]
        chunks.append(chunk)
    
    return chunks


def generate_summary(chunk_text, user_question):
    prompt = f"Assume you are an Apache Pinot Expert. Summarise the following documentation to extract useful information to answer user questions {user_question}. Priority should be given to configuration mentioned in the documentation. {config_prompt}. Also give priority to information that can help in answering: {user_question}.  Documentation: {encoding.decode(chunk_text)}"
    messages = [{"role": "system", "content": "This is Apache Pinot documentation summarization. DO NOT MAKE ANY CHANGES TO CONFIGURATION MENTIONED IN THE DOCUMENTATION. YOU CAN ONLY TRIM IT BUT NOT CHANGE KEYS AND VALUES. YOU ARE ALSO NOT ALLOWED TO MERGE MULTIPLE CONFIGURATIONS"}]    
    messages.append({"role": "user", "content": prompt})

    response = openai.ChatCompletion.create(
            model=MODEL_ENGINE,
            messages=messages,
            temperature=MODEL_TEMPERATURE,
            max_tokens=CHUNK_SUMMARY_LENGTH,
            frequency_penalty=FREQUENCY_PENALTY,
            presence_penalty=PRESENCE_PENALTY
    )

    return response["choices"][0]["message"]['content'].strip()


def consolidate_summaries(summary_list, user_question):
    #TODO: Handle edge case where summary itself breches token limits
    prompt = f"Assume you are an Apache Pinot expert. Consolidate these documentation summaries into a single big summary to answer user questions {user_question}. Give priority to configurations mentioned in the documentation. {config_prompt}. Also give priority to information that can help in answering: {user_question}. Documenation: {str(summary_list)}"

    messages = [{"role": "system", "content": "This is Apache Pinot documentation summarization. DO NOT MAKE ANY CHANGES TO CONFIGURATION MENTIONED IN THE DOCUMENTATION. YOU CAN ONLY TRIM IT BUT NOT CHANGE KEYS AND VALUES. YOU ARE ALSO NOT ALLOWED TO MERGE MULTIPLE CONFIGURATIONS"}]  

    prompt = prompt[:3100]
    messages.append({"role": "user", "content": prompt})

    response = openai.ChatCompletion.create(
            model=MODEL_ENGINE,
            messages=messages,
            temperature=MODEL_TEMPERATURE,
            max_tokens=3100,
            frequency_penalty=FREQUENCY_PENALTY,
            presence_penalty=PRESENCE_PENALTY
        )
    return response["choices"][0]["message"]['content'].strip()
    

def ask_gpt_using_summaries(document_text, user_question):
    prompt = f"Assume you are an Apache Pinot expert. Can you help find the relevant information and configuration from the documentation to answer this user question? \n\n User question: {user_question}.  The response should be of the format \n\n `Answer:` followed by user answer \n\n `Configuration`: followed by a configuration example. \n\n\n. Use configuration similar to the one in the documentation. \n\n DO NOT MAKE ANY CHANGES TO CONFIGURATION MENTIONED IN THE DOCUMENTATION. YOU CAN ONLY TRIM IT BUT NOT CHANGE KEYS AND VALUES. YOU ARE ALSO NOT ALLOWED TO MERGE MULTIPLE CONFIGURATIONS. {config_prompt} \n\n The summarised documentation to answer these questions is presentation in next few chat messages"

    chunks = break_up_text_to_chunks(document_text)
    summary_list = []
    for chunk in chunks:
        summary = generate_summary(chunk, user_question)
        summary_list.append(summary)
    
    print("SUMMARY LIST")
    print(summary_list)
    summarised_doc = consolidate_summaries(summary_list, user_question)

    print("CONSOLIDATED SUMMARY")
    print(summarised_doc)

    messages = [{"role": "user", "content": prompt}]
    messages.append({"role": "user", "content": f"Documentation: {summarised_doc}"})

    completions= openai.ChatCompletion.create(
        model=MODEL_ENGINE,
        messages=messages,
        temperature=MODEL_TEMPERATURE,
        max_tokens=RESPONSE_TOKEN_MAX,
        frequency_penalty=FREQUENCY_PENALTY,
        presence_penalty=PRESENCE_PENALTY
        )

    return completions.choices[0]['message']['content'].strip()


def ask_gpt(documents, user_question):
    # prompt = f"Can you help me find the relevant information and code samples in this documentation to answer this user question? \n\n User question: {user_question}\n\nDocuments:\n\n{documents[:MAX_DOC_LENGTH]}\n\nAnswer:"
    prompt_with_code = f"Can you help me find the relevant information, code samples as well as from the documentation to answer this user question? \n\n User question: {user_question}.  The response should be of the format \n\n `Answer:` followed by user answer \n\n `Configuration`: followed by JSON or YAML configuration example \n\n `Code Sample`: followed by the code sample in JAVA langauge \n\n\n. Use configuration similar to the one in the documentation, also in same format. \n\n The documentation to answer these questions is presentation in next few chat messages"

    prompt_without_code = f"Assume you are an Apache Pinot expert. Can you help find the relevant information and configuration from the documentation to answer this user question? \n\n User question: {user_question}.  The response should be of the format \n\n `Answer:` followed by user answer \n\n `Configuration`: followed by a configuration example. \n\n\n. Use configuration similar to the one in the documentation. Do not change the config format. \n\n The documentation to answer these questions is presentation in next few chat messages"

    prompt = prompt_without_code

    num_chunk = 0
    messages = [{"role": "user", "content": prompt}]
    while (num_chunk * CHUNK_LENGTH < len(documents)):
        start_index = num_chunk * CHUNK_LENGTH
        end_index = (num_chunk + 1) * CHUNK_LENGTH

        if (start_index > 4096 - len(prompt)): 
            break

        if (end_index > 4096 - len(prompt)): 
            end_index = 4096 - len(prompt)
        
        
        if (len(documents) < end_index):
            end_index = len(documents)
        
        messages.append({"role": "user", "content": f"Documentation Part {num_chunk}: {documents[start_index:end_index]}"})
        print(f"Added Chunk: {num_chunk}")
        num_chunk += 1

    completions= openai.ChatCompletion.create(
        model=MODEL_ENGINE,
        messages=messages,
        temperature=MODEL_TEMPERATURE,
        max_tokens=RESPONSE_TOKEN_MAX,
        frequency_penalty=FREQUENCY_PENALTY,
        presence_penalty=PRESENCE_PENALTY
        )

    natural_language_answer = completions.choices[0]['message']['content'].strip()
    return natural_language_answer