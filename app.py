# app.py — Stylish web-based chatbot with memory and mode selection
import gradio as gr
from chat_core import ChatEngine

from tts import speak
from gtts import gTTS


# Initialize chat engine
ce = ChatEngine()

# Session memory: keeps track of conversation per user session
session_history = []

def chat_function(user_input, selected_mode):
    # Append user input to memory
    session_history.append({"role": "user", "content": user_input})
    
    # Get response from ChatEngine
    reply = ce.respond(user_input, mode=selected_mode)
    
    # Append assistant reply to memory
    session_history.append({"role": "assistant", "content": reply})
    
    # Format conversation history with chat bubbles
    history_html = ""
    for msg in session_history:
        if msg["role"] == "user":
            history_html += f"""
            <div class='bubble user'>{msg['content']}</div>
            """
        else:
            history_html += f"""
            <div class='bubble bot'>{msg['content']}</div>
            """
    
    # Return scrollable container
    return f"<div class='chat-container'>{history_html}</div>"

with gr.Blocks() as demo:
    # Title
    gr.Markdown("## 🧠 Chatbot with Memory and Modes")

    # Mode selector dropdown
    mode_selector = gr.Dropdown(["chat", "code", "knowledge"], label="Select Mode", value="chat")

    # Textbox for user input
    user_input = gr.Textbox(label="Your Message", placeholder="Type your question here...")

    # Checkbox to enable TTS
    tts_toggle = gr.Checkbox(label="Enable Voice Output (TTS)", value=False)

    # HTML container for chat history
    chatbot_output = gr.HTML("<div id='chatbox'></div>", elem_id="chatbox")

    # Submit event
    user_input.submit(chat_function, [user_input, mode_selector, tts_toggle], chatbot_output)


# Custom CSS styling
css = """
/* Hide Gradio footer */
footer {visibility: hidden !important;}

/* Body styling */
body {
    background-color: #f5f7fa;
    font-family: 'Segoe UI', Tahoma, sans-serif;
}

/* Page header */
h1 {
    text-align: center;
    color: #333;
    margin-bottom: 20px;
}

/* Chat container */
.chat-container {
    max-height: 500px;
    overflow-y: auto;
    padding: 15px;
    border-radius: 15px;
    background-color: #e0e4eb;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.1);
}

/* Chat bubbles */
.bubble {
    padding: 12px 18px;
    margin: 8px;
    border-radius: 20px;
    max-width: 70%;
    word-wrap: break-word;
    font-size: 14px;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.15);
    transition: transform 0.1s ease, box-shadow 0.2s ease;
}

/* Hover effect on bubbles */
.bubble:hover {
    transform: translateY(-2px);
    box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
}

/* User bubble */
.user {
    background-color: #FFD60A;
    color: #333;
    margin-left: auto;
    text-align: right;
}

/* Bot bubble */
.bot {
    background-color: #333;
    color: #fff;
    margin-right: auto;
    text-align: left;
}

/* Dropdown and input styling */
.gr-dropdown, .gr-textbox {
    border-radius: 8px !important;
    padding: 6px !important;
    margin-bottom: 10px !important;
}

/* Add subtle shadow to input boxes */
.gr-dropdown select, .gr-textbox textarea {
    box-shadow: 0px 2px 6px rgba(0,0,0,0.1);
}

/* Chat container scrollbar styling */
.chat-container::-webkit-scrollbar {
    width: 8px;
}

.chat-container::-webkit-scrollbar-thumb {
    background-color: rgba(0,0,0,0.2);
    border-radius: 4px;
}
"""

with gr.Blocks(css=css) as demo:
    gr.Markdown("## 🧠 Chatbot ")
    
    mode_selector = gr.Dropdown(["chat", "code", "knowledge"], label="Select Mode", value="chat")
    user_input = gr.Textbox(label="Your Message", placeholder="Type your question here...")
    chatbot_output = gr.HTML("<div id='chatbox'></div>", elem_id="chatbox")
    
    user_input.submit(chat_function, [user_input, mode_selector], chatbot_output)

demo.launch()
with gr.Blocks(css="""
/* Header styling */
.header {
    text-align: center;
    font-weight: 800;                     /* Bold */
    font-family: 'Poppins', sans-serif;   /* Elegant font */
    font-size: 40px;                      /* Large font */
    background: linear-gradient(90deg, #FF6B6B, #FFD60A, #4ECDC4); /* Gradient color */
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 30px;
}
""") as demo:
    gr.Markdown("## 🧠Chatbot ")
    
   