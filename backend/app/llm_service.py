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

def extract_specific_detail(user_message: str, detail_name: str) -> dict:
    # This function remains the same and is still very useful.
    prompt = f"""
    You are an expert data extractor. The user was asked for the email's "{detail_name}".
    From the user's response below, extract the value for the "{detail_name}".
    Your entire response must be a simple JSON object containing ONLY the key you found.
    For example: {{"{detail_name}": "the extracted value"}}
    Do not add any other text, explanations, or markdown formatting.

    **User's response:**
    "{user_message}"
    """
    try:
        response = model.generate_content(prompt)
        response_text = response.text
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
            json_block = match.group(0)
            return json.loads(json_block.strip())
        else:
            return {}
    except Exception as e:
        print(f"Error extracting '{detail_name}' with Gemini: {e}")
        return {}

def generate_email_body(details: EmailDetails) -> dict:
    """
    Generates a subject and body for the email using the Gemini API.
    Returns a dictionary with 'subject' and 'body'.
    """
    # --- MODIFIED: More detailed prompt for better content generation ---
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
            # Fallback if JSON is not returned correctly
            return {"subject": details.subject, "body": details.context_details}
    except Exception as e:
        print(f"Error generating email body with Gemini: {e}")
        return {"subject": "Request", "body": "As per our conversation."}
