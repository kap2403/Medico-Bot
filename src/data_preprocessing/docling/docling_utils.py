"""
convert Docling documents to Langchain documents
1. Extract images and tables from the Docling document.
2. Extract the text from the Docling document.
3. Create Langchain documents from the extracted images, tables, and text.
4. save the data in json file.
"""
import json
import os
import itertools
from uuid import uuid4

from docling.document_converter import DocumentConverter
from docling_core.types.doc.document import TableItem,PictureItem
from docling_core.types.doc.labels import DocItemLabel
from langchain_core.documents import Document
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker

import logging

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

        main_ref = ",".join([item.get_ref().cref for item in items])
        parent_ref = ",".join([item.parent.get_ref().cref for item in items])
        child_ref = ",".join([str(child) for sublist in [item.children for item in items] for child in sublist])

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

def extract_all_text(docling_document: DocumentConverter, 
                     file_name: str,
                     medical_specialty: str) -> list[Document]:
    """To exract all the text from the docling document and convert it to langchain 
    document. This is useful for creating a vector store from the text.

    Args:
        docling_document (DocumentConverter): _docling_document_
        file_name (str): name of the file
        medical_specialty (str): book category

    Returns:
        list[Document]: _list of langchain documents_
    """

    documents_list = list()
    for text in docling_document.texts:
        content = text.text
        main_ref = " ".join([text.get_ref().cref])
        parent_ref = " ".join([text.parent.get_ref().cref])
        child_ref = ", ".join([ref.get_ref().cref for ref in text.children])
        document = Document(page_content=content, metadata={
            "source": file_name,
            "chunk_index": None,
            "self_ref": {main_ref},
            "parent_ref": {parent_ref},
            "child_ref": {child_ref},
            "chunk_type": "text",
            "medical_specialty" : medical_specialty,
            "reference": None
        })

        documents_list.append(document)
    return documents_list


def extract_tables(docling_document: DocumentConverter, 
                     file_name: str,
                     medical_specialty: str) -> list[Document]:
    """Extract the tables from the converted document and add metadata.

    Args:
        document (DocumentConverter): converted document.
        file_name (str): file name.
        medical_specialty (str): book category
    Returns:
        list[TableItem]: A list of documents containing table data with 
        reference IDs in the metadata.
    """
    tables: list[Document] = []
    for table in docling_document.tables:
        if table.label in [DocItemLabel.TABLE]:
            main_ref = " ".join([table.get_ref().cref])
            parent_ref = " ".join([table.parent.get_ref().cref])
            child_ref = table.children 

            text = table.export_to_markdown()
            metadata = {
                "source": file_name,
                "chunk_index": None,
                "self_ref": main_ref,
                "parent_ref": parent_ref,
                "child_ref": child_ref,
                "chunk_type": "table",
                "medical_specialty" : medical_specialty,
            }
            document = Document(page_content=text, metadata=metadata)
            tables.append(document)
    return tables


def extract_text_ids(data: dict) -> list:
    """
    Extract all references from a dictionary and return a list of numbers
    from any '#/texts/{number}' references.

    Args:
        data (dict): The dictionary to extract from.

    Returns:
        list: List of integers extracted from '#/texts/{number}' refs.
    """
    refs = [v for k, v in data.items() if k.endswith('_ref') and isinstance(v, str)]
    text_ids = [int(ref.split('/')[2]) for ref in refs if ref.startswith('#/texts/')]
    return text_ids


def save_json(file_path: str, category: str,data: list[Document]) -> None:
    """Save the data in json format.

    Args:
        file_path (str): path of the file.
        data (list[Document]): list of documents.
    """
    doc_dicts = [{"content": doc.page_content, "metadata": doc.metadata} for doc in data]
    with open(f"{file_path}/{category}.json", "w") as f:
        json.dump(doc_dicts, f)


# def main(file_path: str, 
#          file_name: str, 
#          save_path: str,
#         ) -> list[Document]:
#     """Main function to convert docling documents to langchain documents.

#     Args:
#         file_path (str): path of the file.
#         file_name (str): name of the file.
#     Returns:
#         list[Document]: list of langchain documents.
#     """
#     # Extract all text from the docling document
#     docling_document = DocumentConverter(file_path)
#     texts = extract_all_text(docling_document, file_name)

#     # Extract tables from the docling document
#     tables = modifying_tables(docling_document, file_name)

#     # Extract images from the docling document
#     # Combine all documents into a single list
#     documents = list(itertools.chain(texts, tables))

#     save_json(save_path, documents)


# if __name__ == "__main__":
#     logging.basicConfig(
#         level=logging.DEBUG,  
#         format='%(asctime)s - %(levelname)s - %(message)s',
#         handlers=[
#             logging.StreamHandler(),  
#             logging.FileHandler("app.log", mode='a')  
#         ]
#     )
#     logging.info("Creating the dataset")
#     main(r"dataset", 
#          file_name="medical_textbook",
#          save_path=r"dataset"
#         )
#     logging.info("Dataset created successfully")
#     logging.info("Dataset saved successfully")