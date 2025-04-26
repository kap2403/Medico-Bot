"""
In the current version images were not considered in the vector database due to some computing power. so there are the utils to extract references from the retrieved documents and search for pictures. if there is any ref match with picture ref the the images are extracted.
"""
import os
import re
import json
from langchain_core.documents import Document
from docling.document_converter import DocumentConverter


def extract_metadata(documents: list[Document])-> list[str]:
    
    references = []
    for doc in documents:
        meta_data = doc.metadata
        self_ref =  meta_data["self_ref"]
        parent_ref = meta_data["parent_ref"]
        if self_ref:
            references.append(self_ref)
        if parent_ref:
            references.append(parent_ref)
    unique_ref = list(set(references))
    return unique_ref


def images_data(docling_document: DocumentConverter)-> dict:
    images_data = {}
    for image in docling_document.pictures:
        self_ref = image.self_ref
        parent_ref = image.parent.cref
        images_data[self_ref] = parent_ref
    return images_data


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


def extract_matching_pictures(ref_list: list, images_dict:dict) -> list[int]:

    def extract_image_numbers(picture_refs):
        image_numbers = [int(ref.split('/')[-1]) for ref in picture_refs]
        return image_numbers

    all_refs = set()
    for ref_string in ref_list:
        refs = ref_string.split(',')
        all_refs.update(refs)

    # Find matching picture keys where the image's value (text ref) is in all_refs
    matching_pictures = [pic for pic, text_ref in images_dict.items() if text_ref in all_refs]

    image_numbers = extract_image_numbers(matching_pictures)        

    return image_numbers

def extract_ref_paths(images_num_list: list[int])-> list[str]:
    folder_path = "/home/kap2403/Desktop/Medico-AI-Bot/converted/ROBBINS-&-COTRAN-PATHOLOGIC-BASIS-OF-DISEASE-10TH-ED-with-image-refs-artifacts"
    paths = []
    for img_num in images_num_list:
        path = find_image_by_number(folder_path = folder_path,
         img_number= img_num)
        paths.append(path)

    return paths


def images_ref_pipeline(retriever):
    with open(r"/home/kap2403/Desktop/Medico-AI-Bot/dataset/pictures.json", "r") as file:
        images_data = json.load(file)
    
    meta_data = extract_metadata(retriever)
    image_numbers = extract_matching_pictures(meta_data, images_data)
    paths_list = extract_ref_paths(image_numbers)

    return paths_list


    