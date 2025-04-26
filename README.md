---
title: Medico-AI-Bot
app_file: src/interface.py
sdk: gradio
sdk_version: 5.23.1
---
# Installation Guide

Follow the steps below to install Tesserocr on your system:

## Step 1: Download the Tesserocr .whl File
1. Visit the following link: [Tesserocr Windows Build Releases](https://github.com/simonflueckiger/tesserocr-windows_build/releases)
2. Download the appropriate `.whl` file based on your system configuration (e.g., 32-bit or 64-bit, Python version).

## Step 2: Install the Package
1. Open a terminal or command prompt.
2. Navigate to the folder where the downloaded `.whl` file is located.
3. Run the following command, replacing `<package_name>` with the actual filename:
   ```sh
   pip install <package_name>.whl
   ```

Once completed, Tesserocr should be successfully installed on your system!

## Dataset
You can access the dataset using the following link:
[Dataset Download](https://drive.google.com/drive/folders/17J2wDTiXFhk9b1HJ-ASTG1WAg3cZeBNu?usp=sharing)

## Required Libraries
Run the following commands to install the necessary dependencies:
```sh
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install docling
```

## Running the Dataset Parser
1. Download the dataset and store it in a folder.
2. Update the file path in `src/unstructured_pdf_parsing.py`:
   ```python
   if __name__ == "__main__":
       main(folder_path=r"F:\llm_bot\dataset\textbooks")
   ```
3. Run the script:
   ```sh
   python src/unstructured_pdf_parsing.py
   ```



# Preprocessing Guide

## Install Required Libraries

Run the following commands to install the necessary dependencies:

```sh
pip install docling
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

## Running the Dataset Parser

### Step 1: Download the Dataset  
Download the dataset and store it in a designated folder.

### Step 2: Update File Path  
Modify the `unstructured_pdf_parsing.py` script to specify the correct dataset folder path:

```python
if __name__ == "__main__":
    main(folder_path=r"F:\llm_bot\dataset\textbooks")
```

### Step 3: Run the Script  
Execute the script using the following command:

```sh
python src/unstructured_pdf_parsing.py
```
```


