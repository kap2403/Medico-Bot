import gradio as gr
import os
import subprocess
import webbrowser
from groq import Groq


# Function to validate and save the API key
def validate_api_key(user_api_key):
    global api_key
    if not user_api_key:
        return "❌ Please enter your Groq Cloud API key."

    try:
        # Initialize Groq client
        client = Groq(api_key=user_api_key)

        # Make a test request
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello"}],
            model="llama3-70b-8192"
        )

        # Save API key to env variable if successful
        api_key = user_api_key
        os.environ["GROQ_API_KEY"] = api_key

        return "✅ API key is valid and saved!"
    except Exception as e:
        return f"❌ Invalid API key: {str(e)}"

# Gradio Interface
with gr.Blocks() as demo:
    gr.Markdown("## 🔐 Enter Your Groq Cloud API Key")
    gr.Markdown("You can create an API key at [Groq Cloud Console](https://console.groq.com/keys)")

    api_key_input = gr.Textbox(label="Groq Cloud API Key", type="password", placeholder="sk-...")
    submit_button = gr.Button("Validate API Key")
    output_text = gr.Textbox(label="Status", interactive=False)

    # Use the validation function on button click
    submit_button.click(fn=validate_api_key, inputs=api_key_input, outputs=output_text)

demo.launch()

