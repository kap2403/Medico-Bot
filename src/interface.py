import os
import base64
import io
from PIL import Image
import gradio as gr
from src.bot.bot import Medibot
from bs4 import BeautifulSoup
import markdown
from src.auth.auth import register_user, login_user
from src.auth.db import initialize_db
from groq import Groq

from src import config


#======================================
#=============utils====================
#======================================

# Helper functions
def markdown_to_plain_text(md_text: str) -> str:
    html = markdown.markdown(md_text)
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text()

# Ensure base64 strings are properly formatted (no newlines/whitespace)
def decode_base64_to_image(base64_string):
    # Clean the string before decoding
    base64_string = base64_string.replace("\n", "").replace(" ", "")
    image_data = base64.b64decode(base64_string)
    return Image.open(io.BytesIO(image_data))


# Step 1: API Key Validation Logic
def validate_api_key(user_api_key):
    global api_key
    if not user_api_key:
        return "❌ Please enter your Groq Cloud API key.", gr.update(visible=True), gr.update(visible=False)

    try:
        client = Groq(api_key=user_api_key)
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello"}],
            model="llama3-70b-8192"
        )

        api_key = user_api_key
        os.environ["GROQ_API_KEY"] = api_key

        return "✅ API key is valid and saved!", gr.update(visible=False), gr.update(visible=True)

    except Exception as e:
        return f"❌ Invalid API key: {str(e)}", gr.update(visible=True), gr.update(visible=False)
    
def handle_login(userid, password, user_api_key):
    if user_api_key:
        # Step 1: Validate API Key first
        try:
            client = Groq(api_key=user_api_key)
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": "Hello"}],
                model="llama3-70b-8192"
            )

            # If API key is valid, proceed to register
            success, msg = register_user(userid, password, user_api_key)
            if success:
                config.api_key = user_api_key
                os.environ["GROQ_API_KEY"] = user_api_key
                return "✅ API Key validated & registered!", gr.update(visible=False), gr.update(visible=True)
            else:
                return msg, gr.update(visible=True), gr.update(visible=False)

        except Exception as e:
            # API key invalid
            return f"❌ Invalid API Key: {str(e)}", gr.update(visible=True), gr.update(visible=False)

    else:
        # User is trying to login
        success, saved_api_key = login_user(userid, password)
        if success:
            config.api_key = saved_api_key
            os.environ["GROQ_API_KEY"] = saved_api_key
            return "✅ Login successful!", gr.update(visible=False), gr.update(visible=True)
        else:
            return "❌ Incorrect userid or password.", gr.update(visible=True), gr.update(visible=False)


#======================================
#=============Interface================
#======================================

class Interface:
    def __init__(self, config_path: str = "src/bot/configs/prompt.toml",
                 metadata_database: str = "database/metadata.csv",
                 faiss_database: str = "database/faiss_index"):
        
        self.bot = Medibot(config_path = config_path,
                      metadata_database = metadata_database,
                      faiss_database = faiss_database,
                      )
    
    def get_answer(self, question: str):
        try:
            answer_md, retrieved_docs, refered_tables, refered_images = self.bot.query(question)

            # Convert answer to markdown display
            answer_display = answer_md

            # Format referenced tables as markdown
            tables_display = "### Referenced Tables:\n\n"
            if refered_tables:
                for table_name, table_content in refered_tables.items():
                    tables_display += f"{table_content}\n\n"
            else:
                tables_display += "_No tables referenced._"

            # Decode images
            # Format images as markdown (base64)
            images_display = []
            if refered_images:
                for image_name, base64_string in refered_images.items():
                    data_uri = f"data:image/png;base64,{base64_string}"
                    images_display.append(f'![]({data_uri})')  # Markdown embedding for images
            else:
                images_display = None

            # Combine retrieved document texts
            retrieved_display = "### Retrieved Documents:\n\n"
            if retrieved_docs:
                for i, doc in enumerate(retrieved_docs):
                    retrieved_display += f"**Doc {i+1}:**\n{doc.page_content}\n\n"
            else:
                retrieved_display += "_No documents retrieved._"

            return answer_display, tables_display, images_display, retrieved_display

        except Exception as e:
            return f"Error: {str(e)}", "", [], ""

        
        