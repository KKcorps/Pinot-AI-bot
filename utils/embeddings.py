import json
from pinecone import Vector
import tiktoken
import os
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from utils.openai_helper import generate_embeddings
from utils.pinecone_helper import get_pinecone_index, query_index
import pinecone
import argparse
import time

MAX_DOC_COUNT = 1000
MAX_TOKENS_PER_BATCH = 4096
MAX_EMBEDDING_TOKENS =  8096

encoding = tiktoken.get_encoding("cl100k_base")

@dataclass_json
@dataclass
class Document:
    index: int
    text: str
    download_url: str
    html_url: str
    tokens: int

def num_tokens_from_string(string: str) -> int:
    num_tokens = len(encoding.encode(string))
    return num_tokens

def get_doc_content(file_path):
    file = open(file_path, 'r')
    data = file.read().replace('\n', '')
    file.close()
    return data

def get_all_docs(search_dir, download_url_prefix, html_url_prefix, start_idx):
    doc_list = []
    # giving file extensions
    ext = ('.md')

    idx = start_idx
    internal_max_doc_count = idx + MAX_DOC_COUNT
    # iterating over directory and subdirectory to get desired result
    for path, dirc, files in os.walk(search_dir):
            if idx >= internal_max_doc_count:
                break
            if ".git" in dirc:
                    continue
            if "release" in path:
                    continue
            for name in files:
                    if "index.md" in name:
                        continue
                    if name.endswith(ext):
                            print([name, path])  # printing file name
                            file_path = f"{path}/{name}"
                            doc_content = get_doc_content(file_path)
                            tokens = num_tokens_from_string(doc_content)
                            relative_file_path = file_path.replace(search_dir, "")
                            download_url = f"{download_url_prefix}/{relative_file_path}"
                            html_url = f"{html_url_prefix}/{relative_file_path[:-3]}"
                            doc = Document(index=idx, text=doc_content, download_url=download_url, html_url=html_url, tokens=tokens)
                            (smaller_doc_list, next_idx) = split_large_document(doc, idx)
                            for small_doc in smaller_doc_list:
                                doc_list.append(small_doc)
                            idx = next_idx
                            if idx >= internal_max_doc_count:
                                break
    return doc_list


def split_large_document(doc: Document, idx: int):
    
    if(num_tokens_from_string(doc.text) < MAX_TOKENS_PER_BATCH ):
        return ([doc], idx + 1)

    words = doc.text.split(" ")
    doc_list = []
    text = ""
    last_token_len = 0
    start_idx = idx
    for word in words:
        token_len = num_tokens_from_string(text + " " + word)
        if (token_len < MAX_TOKENS_PER_BATCH):
            text = text + " " + word
            last_token_len = token_len
        else:
            doc_list.append(Document(index=start_idx, text=text, download_url=doc.download_url, html_url=doc.html_url, tokens=last_token_len))
            start_idx = start_idx + 1
            text = ""
            last_token_len = 0
    
    if text != "":
        doc_list.append(Document(index=start_idx, text=text, download_url=doc.download_url, html_url=doc.html_url, tokens=last_token_len))
        start_idx = start_idx + 1

    return (doc_list, start_idx)

def batch_documents(book: list[Document]) -> list[list[Document]]:
    book.sort(key=lambda x: x.index)

    batches: list[list[Document]] = []
    for doc in book:
        batches.append([doc])
        # if doc.tokens + sum([x.tokens for x in batches[-1]]) < MAX_TOKENS_PER_BATCH:
        #     batches[-1].append(doc)
        # else:
        #     batches.append([doc])
    
    return batches

def save_embeddings_to_index(embeddings, metadata, ids):

    vectors = []
    MAX_VECTORS_PER_CALL = 10
    for i in range(len(embeddings)):
        idx_mt = metadata[i]
        idx_mt_str = {}
        for k in idx_mt:
            idx_dict = json.loads(idx_mt[k])
            del idx_dict["text"]
            del idx_dict["tokens"]
            idx_mt_str["ids_" + str(k)] = json.dumps(idx_dict)
        
        vectors.append(Vector(id=ids[i], values=embeddings[i], metadata=idx_mt_str))
        if i % MAX_VECTORS_PER_CALL == 0:
            get_pinecone_index().upsert(vectors=vectors)
            print(f"SAVED {i + 1} VECTORS TO PINECONE, TOTAL VECTORS: {len(embeddings)}")
            vectors = []
    
    if len(vectors) != 0:
        get_pinecone_index().upsert(vectors=vectors)
    print(f"SAVED ALL VECTORS TO PINECONE")



if __name__ == "__main__":
    import sys

    parser = argparse.ArgumentParser(
                    prog = 'Generate Pinot Doc Embeddings',
                    description = 'Input doc directory to generate embeddings of markdown files')
    parser.add_argument('-d', '--directory')
    parser.add_argument('-c', '--cache_file')
    parser.add_argument('-q', '--query')
    parser.add_argument('-rc', '--read_from_cache')
    parser.add_argument('--download_url_prefix')
    parser.add_argument('--website_url_prefix')
    parser.add_argument('--max_docs')
    parser.add_argument('--start_id')

    parser.add_argument('-v', '--verbose')

    args = parser.parse_args()

    if args.query is not None:
        query_index(args.query)
        sys.exit(0)

    if args.cache_file is not None:
        cache = args.cache_file
    else:
        cache = f"./scratch/cache_{int(time.time())}.json"

    if args.max_docs is not None:
        MAX_DOC_COUNT = int(args.max_docs)
    
    start_id = 0
    if args.start_id is not None:
        start_id = int(args.start_id)
    
    if args.read_from_cache is None:
        if args.directory is None:
            print("Directory path needs to be set using -d when not using cache")
            sys.exit(1)
        if args.download_url_prefix is None or args.website_url_prefix is None:
            print("Download url prefix and website url prefix need to be set")
            sys.exit(1)
        doc_list = get_all_docs(args.directory, args.download_url_prefix, args.website_url_prefix, start_id)
        batched_docs = batch_documents(doc_list)
        batch_doc_text = []
        for batch in batched_docs:
            combined_text = " ".join([x.text for x in batch])
            num_tokens = num_tokens_from_string(combined_text)
            if num_tokens > MAX_EMBEDDING_TOKENS:
                print(f"NUM TOKENS: {num_tokens}, TEXT: {combined_text}")
                sys.exit(0)
            # assert not (num_tokens_from_string(combined_text) > MAX_EMBEDDING_TOKENS)
            batch_doc_text.append(combined_text)

        embeddings_list = []
        for i in range(0, len(batch_doc_text), 100):
            embeddings_list.extend(generate_embeddings(batch_doc_text[i:i+100]))
        
        batched_metadata = [{x.index: x.to_json() for x in y} for y in batched_docs]
        ids = ["_".join([str(x.index) for x in y]) for y in batched_docs]

        master = list()
        for y in range(len(embeddings_list)):
            master.append(
                {"id": ids[y], "values": embeddings_list[y], "metadata": batched_metadata[y]}
            )

        with open(cache, "w") as f:
            json.dump(master, f)
        
        save_embeddings_to_index(embeddings_list, batched_metadata, ids)
    else:
        with open(cache, "r") as f:
            master = json.load(f)

        save_embeddings_to_index(
            [x["values"] for x in master],
            [x["metadata"] for x in master],
            [x["id"] for x in master],
        )
    print("SAVED METADATA IN PINECONE")

