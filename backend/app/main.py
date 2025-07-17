# backend/app/main.py
import asyncio
import logging
import traceback
import subprocess
import sys
import json
import os
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Import our AI logic
from .llm_service import extract_specific_detail, generate_email_body
from .agent_logic import EmailDetails

# (The initial setup is the same)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(title="Conversational Browser Agent Backend")

# We will use a wildcard for now to ensure no CORS issues during development
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def run_browser_automation(recipient: str, subject: str, body: str) -> str:
    # This function remains unchanged.
    command = [sys.executable, "-u", "app/browser_controller.py", recipient, subject, body]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
    
    if result.returncode != 0:
        logger.error(f"Subprocess failed with exit code {result.returncode}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, command, output=result.stdout, stderr=result.stderr)
    
    return result.stdout


async def send_json_message(websocket: WebSocket, message_type: str, content: str):
    """Helper to send a JSON message with a specific type to the client."""
    message = {"type": message_type, "content": content}
    await websocket.send_text(json.dumps(message))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established.")
    
    conversation_state = EmailDetails()
    # --- MODIFIED: New initial prompt ---
    await send_json_message(websocket, "status", "Hello! I'm your AI assistant. What should I call you?")
    
    try:
        while True:
            user_message = await websocket.receive_text()
            logger.info(f"Received message: {user_message}")
            
            # --- NEW: Ask for name as the first step ---
            if not conversation_state.user_name:
                conversation_state.user_name = user_message.strip()
                await send_json_message(websocket, "status", f"Nice to meet you, {conversation_state.user_name}! I can help you send emails. What is this email about?")
                continue # Wait for the next message

            # (The rest of the logic is shifted into elif blocks)
            elif not conversation_state.primary_reason:
                extracted_data = extract_specific_detail(user_message, "primary_reason")
                if "primary_reason" in extracted_data:
                    conversation_state.primary_reason = extracted_data["primary_reason"]
                    conversation_state.context_details = user_message
            elif not conversation_state.recipient_email:
                extracted_data = extract_specific_detail(user_message, "recipient_email")
                if "recipient_email" in extracted_data:
                    email = extracted_data["recipient_email"]
                    if "@" in email and "." in email:
                         conversation_state.recipient_email = email
            elif not conversation_state.subject:
                extracted_data = extract_specific_detail(user_message, "subject")
                if "subject" in extracted_data:
                    conversation_state.subject = extracted_data["subject"]

            if conversation_state.is_complete_for_sending():
                # This entire block for sending the email remains the same
                await send_json_message(websocket, "status", "Perfect, I have all the details.")
                await send_json_message(websocket, "status", "Generating the email draft now...")
                email_body = generate_email_body(conversation_state)
                draft_msg = f"Draft complete. I will now start the browser to send the email to {conversation_state.recipient_email}."
                await send_json_message(websocket, "status", draft_msg)

                try:
                    browser_output = await asyncio.to_thread(
                        run_browser_automation, 
                        conversation_state.recipient_email, 
                        conversation_state.subject, 
                        email_body
                    )
                    
                    for line in browser_output.strip().split('\n'):
                        if line.startswith("STATUS::"):
                            await send_json_message(websocket, "status", line.replace("STATUS::", "").strip())
                        elif line.startswith("SCREENSHOT::"):
                            filepath = line.replace("SCREENSHOT::", "").strip()
                            try:
                                with open(filepath, "rb") as image_file:
                                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                                await send_json_message(websocket, "image", f"data:image/jpeg;base64,{encoded_string}")
                                os.remove(filepath)
                            except FileNotFoundError:
                                logger.error(f"Screenshot file not found: {filepath}")

                    await send_json_message(websocket, "status", "✅ Browser automation complete!")
                    
                    conversation_state = EmailDetails()
                    await send_json_message(websocket, "status", "What can I do for you next?")
                    
                except Exception as e:
                    logger.error("Error during browser automation:")
                    traceback.print_exc()
                    await send_json_message(websocket, "status", f"❌ An error occurred during browser automation: {e}")
            else:
                # This block for asking the next question also remains the same
                if not conversation_state.primary_reason:
                    await send_json_message(websocket, "status", "I had a little trouble understanding. What is this email about?")
                elif not conversation_state.recipient_email:
                    await send_json_message(websocket, "status", "Got it. And who is the recipient? Please provide their email address.")
                elif not conversation_state.subject:
                    await send_json_message(websocket, "status", "Okay, and what should the subject line be?")

    except WebSocketDisconnect:
        logger.info("Client disconnected.")
    except Exception as e:
        logger.error(f"Error in WebSocket: {e}")
        traceback.print_exc()