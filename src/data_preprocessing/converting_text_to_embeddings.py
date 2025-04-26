# This module is responsible for converting text data into embeddings using the 
# OpenAI API and storing in Faiss database.

import faiss
import tiktoken
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from typing import List, Tuple
from uuid import uuid4
from dotenv import load_dotenv
import logging
# other imports
from dataloader import dataloader

logging.basicConfig(level=logging.INFO)

def main(folder_path: str)-> None:
    """
    Main function to convert text data into embeddings and store them in a Faiss database.
    The function uses the OpenAI API to generate embeddings and the Faiss library 
    to manage the index.

    Args:
        folder_path (str): path to the folder containing the data files.
    """
    logging.info("Loading environment variables...")
    load_dotenv()  # Load environment variables from .env file
    logging.info("Environment variables loaded.")
    logging.info("Loading OpenAI embeddings...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    logging.info("OpenAI embeddings loaded.")
    logging.info("Creating Faiss index...")

    # Create a Faiss inde
    index = faiss.IndexFlatL2(len(embeddings.embed_query("hello world")))
    # load the emcoder to calculate the number of tokens
    enc = tiktoken.get_encoding("cl100k_base")


    vector_store = FAISS(
        embedding_function=embeddings,
        index=index,
        docstore=InMemoryDocstore(),
        index_to_docstore_id={},
        )
    logging.info("Faiss index created.")
    logging.info("Loading data from folder...")
    # Load the data
    chunks_list, _, _, _ = dataloader(folder_path)
    logging.info(f"Loaded {len(chunks_list)} chunks from folder: {folder_path}")
    # calculte the number of tokens
    total_tokens = sum(len(enc.encode(doc.page_content)) for doc in chunks_list)
    cost = (total_tokens / 1000000) * 0.13
    logging.info(f"Total tokens: {total_tokens}")
    logging.info(f"Estimated cost of using text-embedding-3-large: ${cost:.2f}")

    # Ask user for confirmation
    proceed = input("Do you want to proceed with embedding and storing the data in Faiss? (yes/no): ").strip().lower()
    if proceed not in ['yes', 'y']:
        logging.info("Operation cancelled by the user.")
        return
    logging.info("Proceeding with embedding and storing the data in Faiss...")

    logging.info("Converting text data to embeddings...")

    # Convert text data to embeddings

    uuids = [str(uuid4()) for _ in range(len(chunks_list))]
    vector_store.add_documents(documents=chunks_list, ids=uuids)
    logging.info("Text data converted to embeddings and stored in Faiss index.")
    vector_store.save_local("faiss_index")
    logging.info("Faiss index saved to local storage.")


if __name__ == "__main__":
    folder_path = "dataset/converted_json_docs"
    main(folder_path)











