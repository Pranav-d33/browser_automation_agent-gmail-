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

# --- MODIFIED: Import the new AI functions ---
from .llm_service import classify_intent, generate_chat_response, generate_email_body
from .agent_logic import EmailDetails

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(title="Conversational Browser Agent Backend")

origins = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def run_browser_automation(user_email: str, user_password: str, recipient: str, subject: str, body: str) -> str:
    # This function remains unchanged
    command = [sys.executable, "-u", "app/browser_controller.py", user_email, user_password, recipient, subject, body]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        logger.error(f"Subprocess failed with exit code {result.returncode}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, command, output=result.stdout, stderr=result.stderr)
    return result.stdout

async def send_json_message(websocket: WebSocket, message_type: str, content: str):
    message = {"type": message_type, "content": content}
    await websocket.send_text(json.dumps(message))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established.")
    
    conversation_state = EmailDetails()
    await send_json_message(websocket, "status", "Hello! I'm your AI assistant. What should I call you?")
    
    try:
        while True:
            user_message = await websocket.receive_text()
            logger.info(f"Received message: {user_message}")

            # --- NEW INTENT-DRIVEN CONVERSATION FLOW ---

            # First, check if we are in the middle of a task.
            # The presence of `primary_reason` indicates we are in the email workflow.
            if conversation_state.primary_reason:
                # --- TASK EXECUTION MODE ---
                if not conversation_state.user_email:
                    conversation_state.user_email = user_message.strip()
                    await send_json_message(websocket, "status", "Thanks! And what's the password for this account?")
                
                elif not conversation_state.user_password:
                    conversation_state.user_password = user_message.strip()
                    await send_json_message(websocket, "status", "Great. Are there any other specific details to include, like dates?")

                elif not conversation_state.context_details:
                    conversation_state.context_details = user_message.strip()
                    await send_json_message(websocket, "status", "Got it. And finally, what's the recipient's email address?")

                elif not conversation_state.recipient_email:
                    conversation_state.recipient_email = user_message.strip()
            
            else:
                # --- NEUTRAL CONVERSATION MODE ---
                if not conversation_state.user_name:
                    conversation_state.user_name = user_message.strip()
                    await send_json_message(websocket, "status", f"Nice to meet you, {conversation_state.user_name}! How can I help you today?")
                else:
                    intent = classify_intent(user_message)
                    if intent == "email_task":
                        conversation_state.primary_reason = user_message.strip()
                        await send_json_message(websocket, "status", "I can help with that. To access your email, I'll need your Gmail address.")
                    else: # general_chat
                        chat_response = generate_chat_response(user_message, conversation_state.user_name)
                        await send_json_message(websocket, "status", chat_response)

            # --- CHECK IF READY FOR AUTOMATION (This runs after every message) ---
            if conversation_state.is_ready_for_automation():
                await send_json_message(websocket, "status", "Perfect! I have all the details. I'll now open Gmail and send the email.")
                
                email_content = generate_email_body(conversation_state)
                conversation_state.subject = email_content.get("subject", "Request")
                email_body = email_content.get("body", conversation_state.context_details)
                
                try:
                    # (The browser automation and screenshot logic remains exactly the same)
                    browser_output = await asyncio.to_thread(
                        run_browser_automation,
                        conversation_state.user_email,
                        conversation_state.user_password,
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

                    await send_json_message(websocket, "status", f"✅ Email sent successfully to {conversation_state.recipient_email}!")
                    
                    # Reset state but keep the user's name for the next conversation
                    user_name = conversation_state.user_name
                    conversation_state = EmailDetails(user_name=user_name)
                    await send_json_message(websocket, "status", f"What else can I do for you, {user_name}?")
                
                except Exception as e:
                    logger.error("Error during browser automation:")
                    traceback.print_exc()
                    await send_json_message(websocket, "status", f"❌ An error occurred during browser automation: {e}")

    except WebSocketDisconnect:
        logger.info("Client disconnected.")
    except Exception as e:
        logger.error(f"Error in WebSocket: {e}")
        traceback.print_exc()
