"""
contains all the functions to extract the tables, images and, text from the converted 
documents.
"""

import os
import re

from typing import List

from docling.chunking import HybridChunker
from docling_core.types.doc.document import TableItem
from langchain_core.documents import Document
from docling_core.types.doc.labels import DocItemLabel

from docling_core.types.doc.document import TableItem
from transformers import AutoTokenizer
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker

__all__ = [
    "sanitize_name",
    "rename_items",
    "find_matching_fig_ref",
    "find_image_by_number",
    "extract_images",
    "extract_tables",
    "extract_texts",
    "find_relevant_folder"
]


def sanitize_name(name:str)-> str:
    """Replace '-', '_', and '–' with a single hyphen '-' and remove extra spaces.

    Args:
        name (str): file or folder name

    Returns:
        str: processed name
    """
     # Replace -, _, – with '-'
    name = re.sub(r'[-_– ]+', '-', name) 
    # Replace multiple spaces with a single space
    name = re.sub(r'\s+', ' ', name).strip()  
    return name

def rename_items(directory:str):
    """Rename all files and folders inside the given directory.

    Args:
        directory (str): file or folder name
    """
    items = os.listdir(directory)  # Get all files and folders inside the directory
    for item in items:
        old_path = os.path.join(directory, item)
        new_name = sanitize_name(item)  # Clean up the name
        new_path = os.path.join(directory, new_name)

        if old_path != new_path:  # Rename only if the name changes
            os.rename(old_path, new_path)
            print(f"Renamed: {old_path} -> {new_path}")

def find_matching_fig_ref(doc1:dict, doc2:dict)-> str|None:
    """Check the texts ids from text chunks metadata and pictures metadata if any id 
    matches then returns the image id.

    Args:
        doc1 (dict): text chunks metadata
        doc2 (dict): picture metadata

    Returns:
        str|None: if similar text id matched in both the metadata then returns the
        figure reference which is figure number. if no match None
    """

    # Extract and split self_ref and parent_ref into sets
    doc1_self_refs = set(doc1['self_ref'].split())  # Split multiple self_refs
    doc1_parent_refs = set(doc1['parent_ref'].split())  # Split multiple parent_refs

    # Extract text_ref and fig_ref from doc2
    doc2_text_ref = doc2['text_ref']
    doc2_fig_ref = doc2['fig_ref']

    # Check if text_ref exists in self_ref or parent_ref
    if doc2_text_ref in doc1_self_refs or doc2_text_ref in doc1_parent_refs:
        return doc2_fig_ref  # Return fig_ref if there's a match
    return None  # No match found

def find_image_by_number(folder_path: str, img_number:int)-> str|None:
    """Search for an image with the specified number in the folder.

    Args:
        folder_path (str): artifacts path where all the images were stored.
        img_number (int): image id

    Returns:
        str|None: image path 
    """
    
    pattern = re.compile(rf"image-0*{img_number}-[a-fA-F0-9]+\.png")  # Regex pattern

    for filename in os.listdir(folder_path):
        if pattern.match(filename):  # Check if the filename matches the pattern
            return os.path.join(folder_path, filename)  # Return full path

    return None  # Return None if no match found

def extract_images(conv_document: Document) -> Document:
    """Extract the images from the converted document and add the metadata.

    Args:
        conv_document (Document): converted document 

    Returns:
        Document: pictures with the metadata.
    """

    pictures: list[Document] = []
    for picture in conv_document.pictures:
        figure_ref = picture.get_ref().cref
        text_ref = picture.parent.get_ref().cref
        document = Document(
                page_content="",
                metadata={
                    "fig_ref": figure_ref,
                    "text_ref": text_ref,
                },)
        pictures.append(document)
    return pictures
  
def extract_tables(document: Document,
                   file_name: str) -> list[TableItem]:
    """Extract the tables from the converted document and add metadata.

    Args:
        document (Document): converted document.
        file_name (str): file name.

    Returns:
        list[TableItem]: A list of documents containing table data with 
        reference IDs in the metadata.
    """
    tables = []
    for table in document.tables:
        if table.label in [DocItemLabel.TABLE]:

            self_refs = table.get_ref().cref
            parent_refs = table.parent.get_ref().cref if table.parent else ""

            text = table.export_to_markdown()
            document = Document(
                page_content=text,
                metadata={
                    "source": file_name,
                    "self_ref": self_refs,
                    "parent_ref": parent_refs,

                },
            )
            tables.append(document)
    return tables

def extract_texts(conv_document: Document, 
                  pictures:List[Document], 
                  images_artifacts: str, 
                  embeddings_tokenizer: AutoTokenizer,
                  file_name: str
                  )-> List[Document]:
    """Extract the text data from converted document and add the image path in the
       metadata.

    Args:
        conv_document (Document): converted document.
        pictures (List[Document]): extracted pictures list.
        images_artifacts (str): artifacts path to extact image path.
        embeddings_tokenizer (AutoTokenizer): tokenizer to chunk the texts.
        file_name (str): file name.

    Returns:
        List[Document]: chunks with updated metadata.
    """
    texts = []
    doc_id = 0
    for chunk in HybridChunker(tokenizer=embeddings_tokenizer).chunk(conv_document):
        items = chunk.meta.doc_items
        self_refs = " ".join(map(lambda item: item.get_ref().cref, items))
        parent_refs = items[0].parent.get_ref().cref if len(items) > 0 else ""
        meta_data_dict = {
            "source": file_name,
            "self_ref": self_refs,
            "parent_ref": parent_refs,
        }

        for picture in pictures:
            fig_metadata = picture.metadata
            fig_ref = find_matching_fig_ref(meta_data_dict, fig_metadata)
            if fig_ref:
                fig_number = int(fig_ref.split("/")[-1])
                image_path = find_image_by_number(images_artifacts, fig_number)
                meta_data_dict["fig_ref"] = image_path
                meta_data_dict["fig_number"] = fig_number

        text = chunk.text
        document = Document(
                page_content=text,
                metadata= meta_data_dict,
            )
        texts.append(document)
    return texts




def find_relevant_folder(folder_path:str)->dict:
    """create a dict with markdown file(key) and 
       artfacts (value).

    Args:
        folder_path (str): folder path where all the converted documents are stored.

    Returns:
        dict: dict with file with artifacts folder
    """
    # Renaming the files and folders by removing the spaces
    rename_items(folder_path)

    # Initialize the dataset dictionary
    dataset_dict = {}

    # Get all files and folders in the directory (do this only once)
    all_items = os.listdir(folder_path)

    # Split files and folders in one pass
    md_files = {file for file in all_items if file.endswith(".md")}
    folders = {folder for folder in all_items if not folder.endswith(".md")}

    # Create a dictionary of folder name splits for efficient matching
    folder_splits = {tuple(folder.split("-")[:-2]): folder for folder in folders}

    for file in md_files:
        file_split = tuple(file.split("-")[:-1])

        # Check if file_split matches any folder's split
        if file_split in folder_splits:
            dataset_dict[file] = folder_splits[file_split]

    return dataset_dict


def extract_ref_text_ids(meta_data):
    all_refs = []

    # Go through all 3 ref fields
    for key in ["self_ref", "parent_ref", "child_ref"]:
        ref_str = meta_data.get(key)
        if ref_str:
            refs = ref_str.split(",")  # split in case of multiple refs
            all_refs.extend(refs)

    # Remove duplicates
    unique_refs = set(all_refs)

    # Extract /texts/ IDs as integers
    text_refs = [int(ref.split("/")[2]) for ref in unique_refs if "/texts/" in ref]

    return text_refs