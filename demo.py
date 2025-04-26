import gradio as gr
import os
from dotenv import load_dotenv
from src.interface import (
    Interface, 
    handle_login,
)
from src import config

# Load environment variables
load_dotenv()

bot = None  # Initially, no bot is created until the user logs in or registers


# Function to handle bot initialization after successful login
def start_bot(userid, password, api_key_input):
    # Run login first and get success
    global bot
    login_status, login_section, chat_section = handle_login(userid, password, api_key_input)
    
    # Initialize the bot after login is successful
    if "successful" in login_status:  # Check for successful login
        bot = Interface()  # Initialize after login success
        return login_status, login_section, chat_section, bot  # Return all sections and bot
    else:
        return login_status, login_section, chat_section, None  # Return failure and no bot

        

def answer(message, history):
    answer_md, tables_display, images_display, retrieved_display = bot.get_answer(message)
    
    # Combine all parts into a single response string for chat
    combined_response = f"{answer_md}\n\n{tables_display}"
    
    # Add images as markdown
    if images_display:
        combined_response += "\n\n" + "\n\n".join(images_display)
    
    return combined_response


# Build Gradio Interface
with gr.Blocks(fill_height=True, fill_width = True) as app:
    # gr.Markdown("# 🧪 MediBot Login & Chat App")

    # Login Section
    with gr.Column(visible=True) as login_section:
        gr.Markdown("## 🔐 Enter Your Groq Cloud API Key")
        gr.Markdown("You can create an API key at [Groq Cloud Console](https://console.groq.com/keys)")
        gr.Markdown("## 🔐 Login or Register")

        userid_input = gr.Textbox(label="UserID")
        password_input = gr.Textbox(label="Password", type="password")
        api_key_input = gr.Textbox(
            label="Groq API Key (only needed for registration)", 
            type="password", 
            placeholder="sk-... (optional)"
        )

        login_btn = gr.Button("Login / Register")
        login_output = gr.Textbox(label="Login Status", interactive=False)

    # Initialize the bot
    # Chat Section (Initially hidden)
    with gr.Column(visible=False) as chat_section:
        gr.ChatInterface(
                        answer,
                        title="🩺 MediBot Chat Interface",
                        examples=["briefly explain me about cancer", "types of skin diseases?"],
                        flagging_options = ['Like', 'Dislike']
                    )


    login_btn.click(
        fn=start_bot,
        inputs=[userid_input, password_input, api_key_input],
        outputs=[login_output, login_section, chat_section]
    )


app.launch(share=True, show_error=True)
