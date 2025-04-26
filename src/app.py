import gradio as gr
import os
from groq import Groq
from PIL import Image
import base64
import io

import base64
import io
from PIL import Image
import gradio as gr
from bot.bot import Medibot
from bs4 import BeautifulSoup
import markdown

from bot.bot import Medibot


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


# Initialize the bot
bot = Medibot()

def get_answer(question: str):
    try:
        answer_md, retrieved_docs, refered_tables, refered_images = bot.query(question)

        # Convert answer to markdown display
        answer_display = answer_md

        # Format referenced tables as markdown
        tables_display = "### Referenced Tables:\n\n"
        if refered_tables:
            for table_name, table_content in refered_tables.items():
                tables_display += f"**{table_name}**\n\n{table_content}\n\n"
        else:
            tables_display += "_No tables referenced._"

        # Decode images
        images_display = []
        if refered_images:
            for image_name, base64_string in refered_images.items():
                image = decode_base64_to_image(base64_string)
                images_display.append(image)
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



bot = Medibot()

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


# Full Gradio Interface
with gr.Blocks() as app:
    gr.Markdown("# 🧪 MediBot Login & Chat App")

    # 👇 Use Column instead of Blocks so we can toggle visibility
    with gr.Column(visible=True) as login_section:
        gr.Markdown("## 🔐 Enter Your Groq Cloud API Key")
        gr.Markdown("You can create an API key at [Groq Cloud Console](https://console.groq.com/keys)")
        api_key_input = gr.Textbox(label="Groq Cloud API Key", type="password", placeholder="sk-...")
        validate_btn = gr.Button("Validate API Key")
        output_text = gr.Textbox(label="Status", interactive=False)

    with gr.Column(visible=False) as chat_section:
        gr.Markdown("## 🩺 MediBot Chat Interface")
        question_input = gr.Textbox(label="Ask a medical question")
        submit_btn = gr.Button("Submit")

        with gr.Tabs():
            with gr.Tab("Answer"):
                answer_output = gr.Markdown()
            with gr.Tab("Tables"):
                tables_output = gr.Markdown()
            with gr.Tab("Images"):
                images_output = gr.Gallery(columns=2, object_fit="contain")
            with gr.Tab("Documents"):
                docs_output = gr.Markdown()

    # 🔁 Show/hide interface on validation
    validate_btn.click(
        fn=validate_api_key,
        inputs=api_key_input,
        outputs=[output_text, login_section, chat_section]
    )

    submit_btn.click(
        fn=get_answer,
        inputs=question_input,
        outputs=[answer_output, tables_output, images_output, docs_output]
    )

app.launch(share=True, show_error=True)
