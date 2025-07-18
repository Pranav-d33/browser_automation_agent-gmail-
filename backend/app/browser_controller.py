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
SCREENSHOT_DIR = Path(__file__).parent / "temp_screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)

def take_screenshot(page, message: str):
    """Takes a screenshot, saves it to a file, and prints the path to stdout."""
    print(f"STATUS::Taking screenshot: {message}")
    filename = f"{uuid.uuid4()}.jpeg"
    filepath = SCREENSHOT_DIR / filename
    page.screenshot(path=filepath, type="jpeg", quality=80)
    print(f"SCREENSHOT::{filepath}")
    sys.stdout.flush()

# --- MODIFIED: Function now accepts user credentials ---
def send_gmail(user_email: str, user_password: str, recipient: str, subject: str, body: str):
    if not user_email or not user_password:
        raise ValueError("User email and password must be provided.")

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context("user_data", headless=False, slow_mo=50)
        page = browser.pages[0]
        page.goto("https://gmail.com/", wait_until="domcontentloaded")
        take_screenshot(page, "Navigated to Gmail homepage.")

        try:
            page.get_by_role("button", name="Compose").wait_for(timeout=7000)
            print("STATUS::Already logged in.")
            take_screenshot(page, "Logged in successfully.")
        except TimeoutError:
            print("STATUS::Login required...")
            try:
                # This handles cases where Google shows a "Choose an account" screen
                page.get_by_role("link", name=f"user {user_email}").click(timeout=5000)
                take_screenshot(page, "Selected existing user account.")
            except TimeoutError:
                page.locator('input[type="email"]').fill(user_email)
                page.get_by_role("button", name="Next").click()
                take_screenshot(page, "Entered email address.")
            
            page.locator('input[type="password"]').fill(user_password)
            page.get_by_role("button", name="Next").click()
            page.get_by_role("button", name="Compose").wait_for(timeout=30000)
            print("STATUS::Login successful.")
            take_screenshot(page, "Login successful, inbox is visible.")
        
        print("STATUS::Clicking 'Compose' button...")
        page.get_by_role("button", name="Compose").click()
        
        compose_dialog = page.locator('[aria-label="New Message"]')
        expect(compose_dialog).to_be_visible(timeout=10000)
        take_screenshot(page, "Compose dialog is open.")
        
        print("STATUS::Filling out email details...")
        compose_dialog.get_by_role("combobox", name="To recipients").fill(recipient)
        compose_dialog.get_by_role("textbox", name="Subject").fill(subject)
        take_screenshot(page, "Recipient and subject fields are filled.")
        
        compose_dialog.get_by_role("textbox", name="Message Body").fill(body)
        take_screenshot(page, "Email body is filled.")

        print("STATUS::Sending email with 'Control+Enter'...")
        page.keyboard.press("Control+Enter")
        
        print(f"STATUS::Email sent to {recipient} successfully!")
        
        expect(page.get_by_text("Message sent")).to_be_visible(timeout=10000)
        print("STATUS::Confirmed 'Message sent' notification.")
        take_screenshot(page, "Email sent confirmation visible.")
        
        browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # --- MODIFIED: Added arguments for user credentials ---
    parser.add_argument("user_email")
    parser.add_argument("user_password")
    parser.add_argument("recipient")
    parser.add_argument("subject")
    parser.add_argument("body")
    args = parser.parse_args()
    
    send_gmail(args.user_email, args.user_password, args.recipient, args.subject, args.body)
