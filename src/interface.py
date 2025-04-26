import base64
import io
from PIL import Image
import gradio as gr
from bot.bot import Medibot
from bs4 import BeautifulSoup
import markdown

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



with gr.Blocks() as iface:
    gr.Markdown("# 🩺 MediBot - Medical Q&A")

    with gr.Row():
        question_input = gr.Textbox(label="Ask a medical question", placeholder="e.g., What are the symptoms of anemia?")
        submit_btn = gr.Button("Submit")

    with gr.Tabs():
        with gr.Tab("Answer"):
            answer_output = gr.Markdown()
        with gr.Tab("Tables"):
            tables_output = gr.Markdown()
        with gr.Tab("Images"):
            images_output = gr.Gallery(
                                        label="Referenced Images",
                                        columns=2,  # Explicit column count
                                        object_fit="contain"  # Proper image scaling
                                    )
        with gr.Tab("Retrieved Docs"):
            retrieved_output = gr.Markdown()

    submit_btn.click(
        fn=get_answer,
        inputs=[question_input],
        outputs=[answer_output, tables_output, images_output, retrieved_output]
    )

iface.launch(share=True, show_error=True)
