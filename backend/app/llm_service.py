# backend/app/llm_service.py
import os
import re
import json
import google.generativeai as genai
from dotenv import load_dotenv
from .agent_logic import EmailDetails

# --- EXPLICITLY LOAD THE .ENV FILE ---
load_dotenv()

# --- CONFIGURE WITH YOUR API KEY ---
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file. Please add it.")
genai.configure(api_key=api_key)

# --- Use a fast, free-tier model ---
model = genai.GenerativeModel('gemini-2.5-flash')

def extract_specific_detail(user_message: str, detail_name: str) -> dict:
    """
    Extracts a single, specific detail from the user's message using the Gemini API.
    'detail_name' can be 'primary_reason', 'recipient_email', or 'subject'.
    """
    
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
        
        # Simple regex to find the JSON object in the response
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
            json_block = match.group(0)
            return json.loads(json_block.strip())
        else:
            return {} # Return empty dict if no JSON found

    except Exception as e:
        print(f"Error extracting '{detail_name}' with Gemini: {e}")
        return {}

def generate_email_body(details: EmailDetails) -> str:
    """Generates the email body using the Gemini API."""
    
    prompt = f"""
    You are a professional assistant writing a concise and clear email.
    The primary reason for the email is: {details.primary_reason}
    Key details to include are: {details.context_details or details.primary_reason}
    Generate a professional email body. Do not include the subject line.
    Start with a suitable greeting like "Dear Sir/Madam,".
    """
    response = model.generate_content(prompt)
    return response.text