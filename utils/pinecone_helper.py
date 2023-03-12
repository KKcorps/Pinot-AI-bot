import pinecone
from pinecone import Vector
from dotenv import load_dotenv
import re
from utils.openai_helper import generate_embeddings
import os
import json


load_dotenv(override=True)

pinecone_key = os.environ["PINECONE_API_KEY"]
pinecone_env = os.environ["PINECONE_REGION"]
pinecone_index_name = "pinot-docs-simplified"

pinecone.init(
    api_key=pinecone_key, environment=pinecone_env
)

pinecone_client = pinecone
embedding_dimensions = 1536

def query_index(query):
    embedding_res = generate_embeddings([query])

    query_embedding = embedding_res[0]
    res = get_pinecone_index().query(query_embedding, top_k=2, include_metadata=True)

    print(res)
    metadata = res["matches"][0]["metadata"]
    metadata_list = [json.loads(metadata[ids]) for ids in metadata]
    print(metadata_list)
    documentation_urls = [(x["download_url"], x["html_url"]) for x in metadata_list]
    return documentation_urls
    ## Hack to get relevant prose from metadata
    # Each embedding has multiple chapters so for now pick the first one
    # chapters = res["matches"][0]["id"].split("_")

def get_pinecone_index():
    if pinecone_index_name not in pinecone_client.list_indexes():
        pinecone_client.create_index(
            pinecone_index_name,
            dimension=embedding_dimensions,
            metric="cosine",
            metadata_config={"indexed": ["download_url", "html_url", "index"]},
        )

    return pinecone_client.Index(pinecone_index_name)
