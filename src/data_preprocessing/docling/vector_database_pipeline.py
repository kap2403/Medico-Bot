"""
To preprocess the data and create a vector database using docling and langchain, 
openai embeddings.
"""
import getpass
import os
from dotenv import load_dotenv
import itertools
from uuid import uuid4

import faiss
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS

from langchain_openai import OpenAIEmbeddings

from docling.document_converter import DocumentConverter
from langchain_huggingface import HuggingFaceEmbeddings
from transformers import AutoTokenizer

from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.types.doc.document import TableItem,PictureItem
from docling_core.types.doc.labels import DocItemLabel
from langchain_core.documents import Document

import logging

load_dotenv()

def adding_metadata_chunks(chunks: HybridChunker, file_name: str, speciality: str) -> list[Document]:
    """Adding metadata to the chunks
    This function processes a list of chunks and adds metadata to each chunk.

    Args:
        chunks (Hybridchunker): The chunks to be processed.
        file_name (str): The name of the file from which the chunks were created.
        specality (str): specalization of the book.

    Returns:
        List[Document]: A list of Document objects with added metadata.
    """
    documents = []
    for idx, chunk in enumerate(chunks):
        items = chunk.meta.doc_items
        if len(items) == 1 and isinstance(items[0], TableItem):
            # If the chunk is a table, we can skip it
            continue

        main_ref = " ".join([item.get_ref().cref for item in items])
        parent_ref = " ".join([item.parent.get_ref().cref for item in items])
        child_ref = " ".join([str(child) for sublist in [item.children for item in items] for child in sublist])

        text = chunk.text # The text of the chunk
        metadata = {
            "source": file_name,
            "specilization": speciality,
            "chunk_index": idx,
            "self_ref": main_ref,
            "parent_ref": parent_ref,
            "child_ref": child_ref,
            "chunk_type": "text",
            
        }
        document = Document(page_content=text, metadata=metadata)
        documents.append(document)
    return documents


def modifying_tables(docling_document, file_name: str, speciality: str) -> list[Document]:
    """Extract the tables from the converted document and add metadata.

    Args:
        document (Document): converted document.
        file_name (str): file name.
        specality (str): specalization of the book.

    Returns:
        list[TableItem]: A list of documents containing table data with 
        reference IDs in the metadata.
    """
    tables: list[Document] = []
    for table in docling_document.tables:
        if table.label in [DocItemLabel.TABLE]:
            main_ref = table.get_ref().cref
            parent_ref = table.parent.get_ref().cref
            child_ref = table.children 

            text = table.export_to_markdown()
            metadata = {
                "source": file_name,
                "chunk_index": None,
                "self_ref": main_ref,
                "parent_ref": parent_ref,
                "child_ref": child_ref,
                "chunk_type": "table",
            }
            document = Document(page_content=text, metadata=metadata)
            tables.append(document)
    return tables


def dataloader(file_path:str, embeddings_model:str) -> list[Document]:

    logging.info("Converting the document to docling format...")
    docling_document = DocumentConverter().convert(source=file_path).document
    file_name = file_path.split("\\")[-1].split(".")[0]
    # Create a hybrid chunker to chunk the document
    embeddings_tokenizer = AutoTokenizer.from_pretrained(embeddings_model)
    logging.info("Chunking the document...")
    chunks = HybridChunker(tokenizer=embeddings_tokenizer).chunk(docling_document)

    # Add metadata to the chunks
    logging.info("Adding metadata to the chunks...")
    texts = adding_metadata_chunks(chunks, file_name)
    logging.info("Modifying tables...")
    tables = modifying_tables(docling_document, file_name)
    # Combine the text and table documents into a single list
    documents = list(itertools.chain(texts, tables))
    logging.info(f"Loaded {len(documents)} documents from {file_name}.")
    return documents


def create_vector_database(documents: list[Document]) -> FAISS:
    """Create a vector database from the documents.

    Args:
        file_path (str): The path to the document file.
        embeddings_model (str): The model name for embeddings.

    Returns:
        list[Document]: A list of Document objects with embeddings.
    """

    logging.info("Creating the vector database...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    index = faiss.IndexFlatL2(len(embeddings.embed_query("hello world")))
    vector_store = FAISS(
                        embedding_function=embeddings,
                        index=index,
                        docstore=InMemoryDocstore(),
                        index_to_docstore_id={},
                    )
    uuids = [str(uuid4()) for _ in range(len(documents))]
    vector_store.add_documents(documents=documents, ids=uuids)
    logging.info("Vector database created successfully.")

    
def main(file_path:str, embeddings_model:str) -> FAISS:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    documents = dataloader(file_path, embeddings_model)
    create_vector_database(documents)


if __name__ == "__main__":
    file_path = r"converted\ROBBINS-&-COTRAN-PATHOLOGIC-BASIS-OF-DISEASE-10TH-ED-with-image-refs.md"
    embeddings_model = "ibm-granite/granite-embedding-125m-english"
    main(file_path, embeddings_model)