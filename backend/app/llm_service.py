# backend/app/llm_service.py
import os
import re
import json
import google.generativeai as genai
from dotenv import load_dotenv
from .agent_logic import EmailDetails

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file. Please add it.")
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-1.5-flash')

def classify_intent(user_message: str) -> str:
    """
    Classifies the user's intent as either 'email_task' or 'general_chat'.
    """
    prompt = f"""
    Analyze the user's message and classify its primary intent.
    Respond with only one of two possible JSON values: {{"intent": "email_task"}} or {{"intent": "general_chat"}}.

    - If the user mentions sending, composing, or anything related to an email, classify it as "email_task".
    - For any other type of message (like greetings, questions, or casual conversation), classify it as "general_chat".

    User's message: "{user_message}"
    """
    try:
        response = model.generate_content(prompt)
        response_text = response.text
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
            json_block = match.group(0)
            data = json.loads(json_block.strip())
            return data.get("intent", "general_chat")
        return "general_chat"
    except Exception as e:
        print(f"Error classifying intent: {e}")
        return "general_chat"

def generate_chat_response(user_message: str, user_name: str = None) -> str:
    """
    Generates a conversational response for general chat.
    """
    name_context = f"The user's name is {user_name}." if user_name else "You don't know the user's name yet."
    
    prompt = f"""
    You are a friendly and helpful conversational AI. 
    {name_context}
    The user just said: "{user_message}"
    
    Provide a brief, natural, and conversational response. Do not offer to perform tasks unless asked.
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating chat response: {e}")
        return "I'm not sure how to respond to that, but I'm here to help!"

# --- The other functions remain for when the agent is in "email_task" mode ---

def generate_email_body(details: EmailDetails) -> dict:
    """
    Generates a subject and body for the email using the Gemini API.
    Returns a dictionary with 'subject' and 'body'.
    """
    prompt = f"""
    You are a professional assistant writing a concise and clear email.
    The user's name is: {details.user_name}
    The primary reason for the email is: {details.primary_reason}
    Other key details provided by the user are: {details.context_details}

    Based on this information:
    1. Generate a suitable, brief subject line.
    2. Generate a professional email body. Do not include the subject line in the body.
    3. Start the body with a suitable greeting (e.g., "Dear Sir/Madam,").
    4. End the body with a suitable closing and the user's name.
    
    Return your response as a simple JSON object with two keys: "subject" and "body".
    For example: {{"subject": "Your generated subject", "body": "Your generated email body."}}
    """
    try:
        response = model.generate_content(prompt)
        response_text = response.text
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
            json_block = match.group(0)
            return json.loads(json_block.strip())
        else:
            return {"subject": details.subject, "body": details.context_details}
    except Exception as e:
        print(f"Error generating email body with Gemini: {e}")
        return {"subject": "Request", "body": "As per our conversation."}
