import gradio as gr
import gradio as gr
from src.auth.auth import handle_login
from src.auth.db import initialize_db
from dotenv import load_dotenv
from src.interface import Interface

# Load environment variables
initialize_db()
load_dotenv()

bot = None  # Initially, no bot is created until the user logs in or registers


def start_bot(userid, password, api_key_input):
    global bot
    login_status = handle_login(userid, password, api_key_input)
    
    if "successful" in login_status:  # Check for successful login
        bot = Interface()  # Initialize after login success
        return (
            login_status,
            gr.update(visible=False),  # Hide login/registration section
            gr.update(visible=True)    # Show chat section
        )
    else:
        return (
            login_status,
            gr.update(visible=True),   # Keep login/registration section visible
            gr.update(visible=False)   # Keep chat section hidden
        )


def answer(message, history):
    answer_md, tables_display, images_display, retrieved_display = bot.get_answer(message)
    
    # Combine all parts into a single response string for chat
    combined_response = f"{answer_md}\n\n{tables_display}"
    
    # Add images as markdown
    if images_display:
        combined_response += "\n\n" + "\n\n".join(images_display)
    
    return combined_response



with gr.Blocks(fill_height=True, fill_width=True) as app:

    with gr.Column(visible=True) as login_register_section:
        gr.Markdown("# 🔐 MediBot Login & Registration")
        with gr.Tabs():
            with gr.TabItem("Login"):
                userid_login = gr.Textbox(label="UserID")
                password_login = gr.Textbox(label="Password", type="password")
                login_btn = gr.Button("Login")
                login_output = gr.Textbox(label="Login Status", interactive=False)

            with gr.TabItem("Register"):
                gr.Markdown("## 🔐 Enter Your Groq Cloud API Key")
                gr.Markdown("You can create an API key at [Groq Cloud Console]"
                "(https://console.groq.com/keys)")
                userid_register = gr.Textbox(label="UserID")
                password_register = gr.Textbox(label="Password", type="password")
                api_key_register = gr.Textbox(
                    label="Groq API Key",
                    type="password",
                    placeholder="sk-... (required)"
                )
                register_btn = gr.Button("Register")
                register_output = gr.Textbox(label="Registration Status", 
                                             interactive=False)

    # Chat Section (Initially hidden)
    with gr.Column(visible=False) as chat_section:
        gr.ChatInterface(
                answer,
                title="🩺 Medico-Bot",
                examples=["briefly explain me about cancer", "types of skin diseases?"],
                flagging_options = ['Like', 'Dislike']
                )


    # Function connections
    login_btn.click(
        start_bot,
        inputs=[userid_login, password_login],
        outputs=[login_output, login_register_section, chat_section]
    )

    register_btn.click(
        start_bot,
        inputs=[userid_register, password_register, api_key_register],
        outputs=[register_output, login_register_section, chat_section]
    )


app.launch(share=True, show_error=True)
