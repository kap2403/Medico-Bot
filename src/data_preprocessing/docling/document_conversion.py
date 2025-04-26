"""
Script to convert all the pdf documents to markdown format in azure.
"""

import logging
import time
from pathlib import Path
import os
import yaml
from azureml.fsspec import AzureMachineLearningFileSystem
import shutil

from concurrent.futures import ThreadPoolExecutor
from docling_core.types.doc import ImageRefMode, PictureItem, TableItem
from docling.backend.docling_parse_v4_backend import DoclingParseV4DocumentBackend
from docling.datamodel.base_models import ConversionStatus, InputFormat
from docling.datamodel.document import ConversionResult
from docling.datamodel.settings import settings
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import ImageRefMode
from huggingface_hub import snapshot_download
from docling.datamodel.settings import settings


from docling.datamodel.pipeline_options import (
            AcceleratorDevice,
            AcceleratorOptions,
            PdfPipelineOptions,
            TesseractCliOcrOptions,
            TableFormerMode,
        )


from indexing import document_indexing
from docling_utils import save_json


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class Docling_Coversion:
    def __init__(self, image_scale=1.0):
        logging.info("Initializing Docling_Coversion with image_scale=%s", image_scale)
        accelerator_options = AcceleratorOptions(
                                num_threads=8, device=AcceleratorDevice.CUDA
                            )

        # Turn on inline debug visualizations:
        settings.debug.visualize_layout = True
        settings.debug.visualize_ocr = True
        settings.debug.visualize_tables = True
        settings.debug.visualize_cells = True


        pipeline_options = PdfPipelineOptions(
            do_ocr=True,
            do_table_structure=True,
            images_scale=image_scale,
            generate_page_images=True,
            generate_picture_images=True,
            accelerator_options=accelerator_options,
            ocr_options=TesseractCliOcrOptions(force_full_page_ocr=True)
        )

        pipeline_options.table_structure_options.do_cell_matching = True
        pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                    backend=DoclingParseV4DocumentBackend,
                )
            }
        )
        logging.info("Docling_Coversion initialized successfully.")

    def document_conversion(self, file_path):
        """Convert a file and return the document object."""
        logging.info("Starting document conversion for file: %s", file_path)
        return self.converter.convert(Path(file_path)).document

    def save_document(self, file_path, output_dir, azure_fs):
        """Convert a file, save the output as markdown with embedded images, 
           and upload to Azure."""
        input_path = Path(file_path)
        logging.info("Processing file: %s", file_path)

        try:
            result = self.converter.convert(input_path)
            doc_name = input_path.stem
            temp_md_file_path = Path(output_dir) / f"{doc_name}-with-images.md"

            docling_document_class = document_indexing(result, 
                                           "ibm-granite/granite-embedding-125m-english",
                                           speciality= input_path.parent.name,
                                           file_name=input_path.stem
                                           )
            tables_doc = docling_document_class.extract_tables()
            images_doc = docling_document_class.extract_images()
            text_doc = docling_document_class.extract_all_text()
            chunks_doc = docling_document_class.create_chunks()

            # Save the extracted data as JSON
            save_json(file_path=output_dir, category="tables", data=tables_doc)
            save_json(file_path=output_dir, category="images", data=images_doc)
            save_json(file_path=output_dir, category="text", data=text_doc)
            save_json(file_path=output_dir, category="chunks", data=chunks_doc)
            logging.info("Saved extracted data as JSON files.")
            
            
            # Save locally first
            result.document.save_as_markdown(temp_md_file_path, image_mode=ImageRefMode.REFERENCED)
            logging.info("Saved locally: %s", temp_md_file_path)

            # Upload to Azure
            azure_output_path = f"converted_docs_json/{doc_name}"
            azure_fs.upload(lpath=str(output_dir), rpath=azure_output_path, recursive=True)
            logging.info("Uploaded to Azure: %s", azure_output_path)

            # Optionally, delete the local file after upload
            if output_dir.exists() and output_dir.is_dir():
                shutil.rmtree(output_dir)
                logging.info("Deleted local directory: %s", output_dir)

        except Exception as e:
            logging.error("Error processing file %s: %s", file_path, e)




def main(source_dir: str):
    
    logging.info("Starting main function with source_dir: %s", source_dir)
    
    # Set the temporary output directory

    # Set the local directory to save PDFs
    local_pdf_dir = Path("./local_pdfs")
    local_pdf_dir.mkdir(parents=True, exist_ok=True)  # Create the directory if it doesn't exist
    logging.info("Local PDF directory created: %s", local_pdf_dir)

    fs = AzureMachineLearningFileSystem(source_dir)
    all_pdf_files = fs.glob('**/*.pdf')  
    logging.info("Found %d PDF files in source directory.", len(all_pdf_files))

    converter = Docling_Coversion(image_scale=2)

    for file_path in all_pdf_files:
        # file_path = Path(file_path)
        output_dir = Path("./temp")
        output_dir.mkdir(parents=True, exist_ok=True)  # Create the directory if it doesn't exist
        logging.info("Temporary output directory created: %s", output_dir)

        file_path_ = Path(file_path)
        file_name = file_path_.name
        local_pdf_path = local_pdf_dir / file_name
        azure_output_path = f"converted_docs_json/{file_path_.stem}"

        # Check if the file already exists in Azure
        if fs.exists(azure_output_path):
            logging.info("Skipping %s, already processed.", file_name)
            continue

        # Save the PDF locally
        logging.info("Downloading file: %s", file_name)
        with fs.open(file_path, "rb") as remote_file:
            with open(local_pdf_path, "wb") as local_file:
                local_file.write(remote_file.read())
        logging.info("File saved locally: %s", local_pdf_path)

        # Process the local PDF file
        logging.info("Processing: %s", file_name)
        converter.save_document(local_pdf_path, output_dir, fs)

        # Optionally, delete the local PDF after processing
        local_pdf_path.unlink()
        logging.info("Deleted local PDF: %s", local_pdf_path)

    logging.info("Processing completed for all files.")


if __name__ == "__main__":
    logging.info("Script started.")
    main(source_dir=(
        'azureml://subscriptions/485363cd-687d-4adb-a30b-35108c11d682/resourcegroups/medbot/workspaces/karthik/datastores/workspaceartifactstore/paths/UI/2025-04-11_075006_UTC/PdfFiles/'
    ))
    logging.info("Script finished.")