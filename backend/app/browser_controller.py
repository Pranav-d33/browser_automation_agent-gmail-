# backend/app/browser_controller.py
import os
import sys
import argparse
import uuid
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError, expect

load_dotenv()

# --- SETUP FOR SCREENSHOTS ---
# Create a temporary directory for screenshots if it doesn't exist
SCREENSHOT_DIR = Path(__file__).parent / "temp_screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)

def take_screenshot(page, message: str):
    """Takes a screenshot, saves it to a file, and prints the path to stdout."""
    print(f"STATUS::Taking screenshot: {message}")
    
    # Generate a unique filename for the screenshot
    filename = f"{uuid.uuid4()}.jpeg"
    filepath = SCREENSHOT_DIR / filename
    
    # Take screenshot and save it to the specified path
    page.screenshot(path=filepath, type="jpeg", quality=80)
    
    # Print the file path with a special prefix for the parent process to capture
    print(f"SCREENSHOT::{filepath}")
    sys.stdout.flush() # Ensure the output is sent immediately

def send_gmail(recipient: str, subject: str, body: str):
    email = os.getenv("TEST_GMAIL_EMAIL")
    password = os.getenv("TEST_GMAIL_PASSWORD")

    if not email or not password:
        raise ValueError("Test email or password not set in .env file.")

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context("user_data", headless=False, slow_mo=50)
        page = browser.pages[0]
        page.goto("https://gmail.com/", wait_until="domcontentloaded")

        try:
            page.get_by_role("button", name="Compose").wait_for(timeout=7000)
            print("STATUS::Already logged in.")
            take_screenshot(page, "Logged in successfully.")
        except TimeoutError:
            print("STATUS::Login required...")
            try:
                page.get_by_role("link", name=f"user {email}").click(timeout=5000)
            except TimeoutError:
                page.locator('input[type="email"]').fill(email)
                page.get_by_role("button", name="Next").click()
            
            page.locator('input[type="password"]').fill(password)
            page.get_by_role("button", name="Next").click()
            page.get_by_role("button", name="Compose").wait_for(timeout=30000)
            print("STATUS::Login successful.")
            take_screenshot(page, "Login successful.")
        
        print("STATUS::Clicking 'Compose' button...")
        page.get_by_role("button", name="Compose").click()
        
        compose_dialog = page.locator('[aria-label="New Message"]')
        expect(compose_dialog).to_be_visible(timeout=10000)
        take_screenshot(page, "Compose dialog is open.")
        
        print("STATUS::Filling out email details...")
        compose_dialog.get_by_role("combobox", name="To recipients").fill(recipient)
        compose_dialog.get_by_role("textbox", name="Subject").fill(subject)
        compose_dialog.get_by_role("textbox", name="Message Body").fill(body)
        take_screenshot(page, "Email fields are filled.")

        print("STATUS::Sending email with 'Control+Enter'...")
        page.keyboard.press("Control+Enter")
        
        print(f"STATUS::Email sent to {recipient} successfully!")
        
        expect(page.get_by_text("Message sent")).to_be_visible(timeout=10000)
        print("STATUS::Confirmed 'Message sent' notification.")
        take_screenshot(page, "Email sent confirmation visible.")
        
        browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("recipient")
    parser.add_argument("subject")
    parser.add_argument("body")
    args = parser.parse_args()
    
    send_gmail(args.recipient, args.subject, args.body)