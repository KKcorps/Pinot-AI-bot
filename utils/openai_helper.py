import openai
import os
from dotenv import load_dotenv
load_dotenv(override=True)

openai.api_key = os.environ["OPEN_AI_KEY"]
MAX_DOC_LENGTH = 2048
CHUNK_LENGTH = 1024
RESPONSE_TOKEN_MAX = 2048

#TODO: Implement a summarise function that can be used after multiple calls

def ask_gpt(documents, user_question):
    # prompt = f"Can you help me find the relevant information and code samples in this documentation to answer this user question? \n\n User question: {user_question}\n\nDocuments:\n\n{documents[:MAX_DOC_LENGTH]}\n\nAnswer:"
    prompt_with_code = f"Can you help me find the relevant information, code samples as well as from the documentation to answer this user question? \n\n User question: {user_question}.  The response should be of the format \n\n `Answer:` followed by user answer \n\n `Configuration`: followed by JSON or YAML configuration example \n\n `Code Sample`: followed by the code sample in JAVA langauge \n\n\n. Use configuration similar to the one in the documentation, also in same format. \n\n The documentation to answer these questions is presentation in next few chat messages"

    prompt_without_code = f"Can you help me find the relevant information and configuration from the documentation to answer this user question? \n\n User question: {user_question}.  The response should be of the format \n\n `Answer:` followed by user answer \n\n `Configuration`: followed by a configuration example. \n\n\n. Use configuration similar to the one in the documentation. Do not change the config format. \n\n The documentation to answer these questions is presentation in next few chat messages"

    prompt = prompt_without_code
    # model_engine = "davinci-codex" # use the codex model for generating code
    # completions = openai.Completion.create(engine=model_engine, prompt=prompt, max_tokens=1024)
    # code_answer = completions.choices[0].text.strip()

    # prompt = f"User question: {user_question}\n\nCode:\n\n{code_answer}\n\nAnswer:"
    model_engine = "gpt-3.5-turbo" # use the instruct-beta model for generating natural language responses
    # completions = openai.Completion.create(engine=model_engine, prompt=prompt, max_tokens=1024)

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
        model=model_engine,
        messages=messages,
        temperature=0.2,
        max_tokens=RESPONSE_TOKEN_MAX,
        frequency_penalty=1.0,
        presence_penalty=1.0
        )

    natural_language_answer = completions.choices[0]['message']['content'].strip()
    return natural_language_answer