import openai
import os
from dotenv import load_dotenv
import re 
import tiktoken

load_dotenv(override=True)

openai.api_key = os.environ["OPEN_AI_KEY"]
MAX_DOC_LENGTH = 2048
CHUNK_LENGTH = 2048
CHUNK_OVERLAP_LENGTH = 128
CHUNK_SUMMARY_LENGTH = 512
CONSOLIDATED_SUMMARY_LENGTH = 3100
RESPONSE_TOKEN_MAX = 512
MODEL_ENGINE = "gpt-3.5-turbo"
MODEL_TEMPERATURE = 0.2
FREQUENCY_PENALTY = 1.0
PRESENCE_PENALTY = 1.0

EMBEDDINGS_MODEL_ENGINE = "text-embedding-ada-002"
MAX_EMBEDDING_TOKENS = 8191

encoding = tiktoken.encoding_for_model(MODEL_ENGINE)

def generate_embeddings(
    batch_doc_text: list[str],
):
    # batch_doc_text = []
    # for batch in batches:
    #     batch_doc_text.append(" ".join([x.text for x in batch]))

    # assert not any([num_tokens_from_string(x) >= MAX_EMBEDDING_TOKENS for x in batch_doc_text])
    res = openai.Embedding.create(input=batch_doc_text, engine=EMBEDDINGS_MODEL_ENGINE)
    return [record["embedding"] for record in res["data"]]



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
    prompt = f"Assume you are an Apache Pinot Expert. Summarise the following documentation to extract useful information to answer user questions {user_question}. Give priority to information that can help in answering: {user_question}.  Documentation: {encoding.decode(chunk_text)}"
    messages = [{"role": "system", "content": "This is Apache Pinot documentation summarization."}]    
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
    prompt = f"Assume you are an Apache Pinot expert. Consolidate these documentation summaries mentioned under `Documentation` into a single big summary. Give priority to information that can help in answering: {user_question}."

    messages = [{"role": "system", "content": "This is Apache Pinot documentation summarization."}]  

    messages.append({"role": "user", "content": prompt})
    #TODO: This 3000 word limit is a hack
    messages.append({"role": "user", "content": f"Documentation: {str(summary_list)[:3000]}"})

    response = openai.ChatCompletion.create(
            model=MODEL_ENGINE,
            messages=messages,
            temperature=MODEL_TEMPERATURE,
            max_tokens=CONSOLIDATED_SUMMARY_LENGTH,
            frequency_penalty=FREQUENCY_PENALTY,
            presence_penalty=PRESENCE_PENALTY
        )
    return response["choices"][0]["message"]['content'].strip()
    

def ask_gpt_using_summaries(document_text, user_question):

    text_without_code_blocks = remove_config_blocks(document_text)
    chunks = break_up_text_to_chunks(text_without_code_blocks)
    summary_list = []
    for chunk in chunks:
        summary = generate_summary(chunk, user_question)
        summary_list.append(summary)
    
    summarised_doc = consolidate_summaries(summary_list, user_question)
   
    messages = []
    message1 = {"role": "user", "content": """
Assume you are an assistant with knowledge about Apache Pinot. Answer any questions about Pinot with the following format -
     \n\n Answer: [answer to the question asked by user]
    \n\n Configuration (Optional): [add the configuration here].
    \n\n User will provide you additional documentation with under heading Documentation: [user documentation here]
    \n\n User will provie you all the configurations mentioned in the documentation under heading Doc_Configuration: [configuration mentioned in docs here]"""}

    message2 = {"role": "user", "content": f"Documentation: {summarised_doc[:2048]}"}
    message3 = {"role": "user", "content": f"Doc_Configuration: {str(extract_code_blocks_with_prefix(document_text))[:1024]}"}
    message4 = {"role": "user", "content": f"{user_question}"}


    messages.append(message1)
    messages.append(message2)
    messages.append(message3)
    messages.append(message4)

    completions= openai.ChatCompletion.create(
        model=MODEL_ENGINE,
        messages=messages,
        temperature=MODEL_TEMPERATURE,
        max_tokens=RESPONSE_TOKEN_MAX,
        frequency_penalty=FREQUENCY_PENALTY,
        presence_penalty=PRESENCE_PENALTY
        )

    return completions.choices[0]['message']['content'].strip()


def extract_code_blocks_with_prefix(markdown_text):
    # Define a regular expression to match code blocks
    code_regex = re.compile(r"```(?:\w+)?\n([\s\S]*?)\n```")

    # Find all matches of code blocks in the text
    matches = code_regex.finditer(markdown_text)

    # Extract the code blocks along with their start indices
    code_blocks = [(match.start(), match.group(1)) for match in matches]

    formatted_code_blocks = []
    for block in code_blocks:
        start_index = block[0]
        block_text = markdown_text[:start_index].strip()
        text_end = block_text.rfind(".")
        text_size = len(block_text[text_end + 1:])
        # 20 is a hack ignore
        if text_size <= 20 and text_end != -1: 
            text_end = block_text.rfind(".", 0, text_end-1)
        
        block_text_last_line = ""
        if text_end != -1:
            block_text_last_line = block_text[text_end + 1:]
        
        formatted_block = f"{block_text_last_line}\n ```{block[1]}```"
        formatted_code_blocks.append(formatted_block)

    return formatted_code_blocks

def remove_config_blocks(markdown_text):
    # Use regex to remove all configuration blocks
    new_markdown_text = re.sub(r'```(.*?)```', '', markdown_text, flags=re.DOTALL)
    return new_markdown_text

if __name__ == "__main__":
    from utils.github_helper import get_doc_content
    doc_url = "https://raw.githubusercontent.com/pinot-contrib/pinot-docs/5e95cbc3771f28bb124e09c4eaba028725168dda/basics/data-import/upsert.md"
    document_text = get_doc_content(doc_url)

    # print(document_text)
    question = "How to enable upsert?"
    answer = ask_gpt_using_summaries(document_text, question)
    print(f"Question: {question} \n\n {answer}")
