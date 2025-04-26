from langchain_core.documents import Document
from typing import Tuple, List
import pandas as pd
import re

class Metadata:
    def __init__(self, ref_database_path: str):
        self.df = pd.read_csv(ref_database_path)

    def extract_ref_from_metadata(self, meta_data: dict) -> List[str]:
        """Extract references from metadata of images and tables."""

        meta_data_dict = {}
        meta_data_dict["source"] = meta_data.get("source", "")
        self_ref = meta_data.get("self_ref", "")
        parent_ref = meta_data.get("parent_ref", "")
        child_ref = meta_data.get("child_ref", "")

        formated_self_ref = re.split(r'[,\s]+', self_ref or "")
        formated_parent_ref = re.split(r'[,\s]+', parent_ref or "")
        formated_child_ref = re.split(r'[,\s]+', child_ref or "")

        filtered_self_ref_ids = [item for item in formated_self_ref 
                                 if item.startswith('#/tables/') or item.startswith('#/pictures/')]
        filtered_parent_ref_ids = [item for item in formated_parent_ref 
                                   if item.startswith('#/tables/') or item.startswith('#/pictures/')]
        filtered_child_ref_ids = [item for item in formated_child_ref 
                                  if item.startswith('#/tables/') or item.startswith('#/pictures/')]

        # Combine all filtered references into a set (to avoid duplicates)
        all_filtered_references = set(filtered_self_ref_ids + 
                                       filtered_parent_ref_ids + 
                                       filtered_child_ref_ids)
        if len(all_filtered_references) > 0:
            meta_data_dict["self_ref"] = list(all_filtered_references)
            return meta_data_dict
        
    def extract_all_ref_from_retrived_chunks(self, chunks: Document) -> dict:
        all_metadata = {}
        # Example: Iterate over documents and add extracted metadata to the new dictionary
        for idx, doc in enumerate(chunks):  # Assuming `docs` is a list of documents
            meta_data = doc.metadata  # Extract metadata from the document
            extracted_ref_data = self.extract_ref_from_metadata(meta_data)  # Extract references
            
            # Add the extracted metadata to the all_metadata dictionary
            if extracted_ref_data:
                all_metadata[f"doc_{idx}"] = extracted_ref_data
            
        return all_metadata


    def get_data_from_ref(self, chunks:Document) -> Tuple[str, str]:
        """Extract tables and pictures from metadata using references."""


        tables = {}
        images = {}

        all_metadata = self.extract_all_ref_from_retrived_chunks(chunks)

        for meta in all_metadata.values():
            source = meta.get("source", "")
            ref = meta.get("self_ref", [])

            for r in ref:
                reference_rows = self.df[
                    (self.df['source'] == source) &
                    (self.df['self_ref'].isin([r]))
                ]

                if not reference_rows.empty:
                    chunk_type = reference_rows["chunk_type"].values[0]
                    page_content = reference_rows["page_content"].values[0]
                    
                    if chunk_type == "table":
                        tables[r] = page_content
                    elif chunk_type == "picture":
                        images[r] = page_content
        
        return tables, images