# this mo

import re
import os
import json
import docling
from langchain_core.documents import Document
from typing import List, Dict, Any, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)

#============================
# data loader from json and md files
#============================

def load_json_file(file_path: str)-> dict:
    """
    Load a JSON file and return its content as a dictionary.

    Args:   
        file_path (str): Path to the JSON file.

    Returns:
        dict: Dictionary containing the JSON data.
    """
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def load_md_file(file_path: str) -> str:
    """
    Load a Markdown file and return its content as a string.
    The function reads the file in UTF-8 encoding.

    Args:
        file_path (str): Path to the Markdown file.

    Returns:
        str: Content of the Markdown file as a string.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content


def data_preprocess(folder_path: str) -> dict:
    """
    Load data from a folder containing JSON files and a Markdown file.
    The function reads the following files:
    - tables.json
    - images.json
    - text.json
    - chunks.json
    - {base_folder_name}-with-images.md

    Args:
        folder_path (str): Path to the folder containing the JSON and Markdown files.

    Returns:
        dict: A dictionary containing the loaded data from the JSON files and the 
        Markdown file.
    """
    tables_path = os.path.join(folder_path, "tables.json")
    images_path = os.path.join(folder_path, "images.json")
    text_path = os.path.join(folder_path, "text.json")
    chunks_path = os.path.join(folder_path, "chunks.json")

    # Extract base folder name for md and images folder
    base_folder_name = os.path.basename(folder_path)
    images_folder_path = os.path.join(folder_path, f"{base_folder_name}-with-images_artifacts")
    md_file_path = os.path.join(folder_path, f"{base_folder_name}-with-images.md")

    # Load JSON contents
    tables = load_json_file(tables_path)
    images = load_json_file(images_path)
    text = load_json_file(text_path)
    chunks = load_json_file(chunks_path)

    # Load Markdown content
    markdown = load_md_file(md_file_path)

    return {
        "tables": tables,
        "images": images,
        "text": text,
        "chunks": chunks,
        "images_folder": images_folder_path,
        "markdown": markdown
    }


def load_json_data_documents(converted_document: dict, data_type: str)-> Document:
    """
    Load JSON data documents from the converted document.
    This function takes a converted document and a data type (e.g., "tables", "images", "text", "chunks")
    and returns a list of Document objects.

    Args:
        converted_document (dict): The converted document containing data.
        data_type (str): The type of data to load (e.g., "tables", "images", "text", "chunks").
    Returns:
        Document: A list of Document objects containing the loaded data.
    """
    documents = []
    for chunk in converted_document[data_type]:
        content = chunk["content"]
        metadata = chunk["metadata"]
        # Create Document object
        document = Document(
            page_content=content,
            metadata=metadata
        )
        documents.append(document)

    return documents



#============================
#  dataloader for all the data
#  from the folder
#  containing json and md files
#  and images
#============================


def dataloader(folder_path: str)-> Tuple[list, list, list, list]:
    """
    Load data from a folder containing JSON files and a Markdown file.
    The function reads the following files:

    Args:
        folder_path (str): Folder path containing all folders with JSON files and 
        Markdown files.
    Returns:
        Tuple[list, list, list, list]: list of chunks, list of pictures, list of tables, 
        and list of text of overall data.
    """

    chunks_list = []
    pictures_list = []
    tables_list = []
    text_list = []

    logging.info(f"Loading data from folder: {folder_path}")
    for file_name in os.listdir(folder_path):
        logging.info(f"Processing file: {file_name}")
        file_path = os.path.join(folder_path, file_name)
        
        # load the data
        dict_data = data_preprocess(file_path)
        chunks_data = load_json_data_documents(dict_data, "chunks")
        pictures_data = load_json_data_documents(dict_data, "images")
        tables_data = load_json_data_documents(dict_data, "tables")
        text_data = load_json_data_documents(dict_data, "text")

        # adding the data to the list
        chunks_list.extend(chunks_data)
        pictures_list.extend(pictures_data)
        tables_list.extend(tables_data)
        text_list.extend(text_data)
        logging.info(f"Loaded {len(chunks_data)} chunks, {len(pictures_data)} pictures, "
                     f"{len(tables_data)} tables, and {len(text_data)} text documents from {file_name}")
    
    return chunks_list, pictures_list, tables_list, text_list



if __name__ == "__main__":
    # Example usage
    folder_path = "dataset/converted_json_docs"
    chunks, pictures, tables, text = dataloader(folder_path)
    