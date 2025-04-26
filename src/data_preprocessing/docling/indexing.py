"""
create chunks and create clusters usign raptor architecture.
"""

import json
import os
import itertools
import logging
from uuid import uuid4

from docling.document_converter import DocumentConverter
from docling_core.experimental.serializer.markdown import MarkdownTableSerializer
from docling_core.transforms.chunker.hierarchical_chunker import ChunkingDocSerializer
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.types.doc.document import DoclingDocument
from docling_core.types.doc.labels import DocItemLabel
from langchain_core.documents import Document
from docling_core.types.doc import ImageRefMode, PictureItem, TableItem

from transformers import AutoTokenizer

# imports from another scripts
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


class document_indexing:
    def __init__(self, 
                 docling_converted_document: DocumentConverter,
                 embeddings_model: str, 
                 speciality: str,
                 file_name: str): 
        # convert the document
        self.converted_document = docling_converted_document.document
        # hybrid chunking
        self.embeddings_tokenizer = AutoTokenizer.from_pretrained(embeddings_model)
        self.speciality = speciality
        self.file_name = file_name

    def create_chunks(self):
        chunks = HybridChunker(tokenizer=self.embeddings_tokenizer).chunk(self.converted_document)
        updated_chunks = adding_metadata_chunks(chunks = chunks, 
                                                file_name = self.file_name , 
                                                speciality = self.speciality) 
        return updated_chunks
    
    def extract_all_text(self) -> list[Document]:
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
        for text in self.converted_document.texts:
            content = text.text
            main_ref = ",".join([text.get_ref().cref])
            parent_ref = ",".join([text.parent.get_ref().cref])
            child_ref = ",".join([ref.get_ref().cref for ref in text.children])
            document = Document(page_content=content, metadata={
                "source": self.file_name,
                "chunk_index": None,
                "self_ref": main_ref,
                "parent_ref": parent_ref,
                "child_ref": child_ref,
                "chunk_type": "text",
                "medical_specialty" : self.speciality,
                "reference": None
            })

            documents_list.append(document)
        return documents_list
    
    def extract_tables(self) -> list[Document]:
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
        for table in self.converted_document.tables:
            if table.label in [DocItemLabel.TABLE]:
                main_ref = ",".join([table.get_ref().cref])
                parent_ref = ",".join([table.parent.get_ref().cref])
                child_ref = ",".join([ref.get_ref().cref for ref in table.children])

                text = table.export_to_markdown()
                metadata = {
                    "source": self.file_name,
                    "chunk_index": None,
                    "self_ref": main_ref,
                    "parent_ref": parent_ref,
                    "child_ref": child_ref,
                    "chunk_type": "table",
                    "medical_specialty" : self.speciality,
                }
                document = Document(page_content=text, metadata=metadata)
                tables.append(document)
        return tables
    
    def extract_images(self) -> list[Document]:
        """Extract the tables from the converted document and add metadata.

        Args:
            document (DocumentConverter): converted document.
            file_name (str): file name.
            medical_specialty (str): book category
        Returns:
            list[TableItem]: A list of documents containing table data with 
            reference IDs in the metadata.
        """
        images: list[Document] = []
        for picture in self.converted_document.pictures:
            if picture.label in [DocItemLabel.PICTURE]:
                main_ref = ",".join([picture.get_ref().cref])
                parent_ref = ",".join([picture.parent.get_ref().cref])
                child_ref = ",".join([ref.get_ref().cref for ref in picture.children])
                metadata = {
                    "source": self.file_name,
                    "chunk_index": None,
                    "self_ref": main_ref,
                    "parent_ref": parent_ref,
                    "child_ref": child_ref,
                    "chunk_type": "table",
                    "medical_specialty" : self.speciality,
                }
                document = Document(page_content=main_ref, metadata=metadata)
                images.append(document)
        return images

    