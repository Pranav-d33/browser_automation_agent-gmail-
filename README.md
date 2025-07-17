Conversational Browser Control Agent
This project is a sophisticated AI agent that controls a web browser through a natural language, conversational interface. The agent demonstrates its capabilities by automating the process of logging into Gmail, composing, and sending an email, all while providing real-time visual feedback to the user.

The user experience is modeled after advanced agentic systems like Proxy Convergence AI, where browser actions are visualized through screenshots embedded directly within the chat flow.

Core Principle: True Browser Automation
A critical requirement of this project is to demonstrate genuine browser automation, not API integration.

This agent controls a real browser instance using Playwright. It navigates the web, clicks UI elements, and types into forms just as a human would.

It does not use any of the following shortcuts:

❌ No Gmail API

❌ No SMTP libraries

❌ No programmatic form submissions via HTTP requests

The entire email-sending process is performed by interacting with the live Gmail web interface, proving the agent's capability to control a browser for complex tasks.

Architecture Diagram
The system is built on a decoupled frontend-backend architecture, ensuring clear separation of concerns and future extensibility.

+-----------------+      +----------------------+      +------------------------+
|                 |      |                      |      |                        |
|  React Frontend |      |     FastAPI Backend  |      |   Browser Controller   |
| (App.jsx)       |      |      (main.py)       |      | (browser_controller.py)|
|                 |      |                      |      |      (Playwright)      |
+-------+---------+      +----------+-----------+      +------------+-----------+
        |                    ^      |     ^                      |
        | WebSocket (ws)     |      |     | (Subprocess Call)    |
        v                    |      |     |                      |
+-------+---------+          |      |     +----------------------+
|                 |          |      |
| User Interface  |----------+      |
| (Chat & Images) |                 |
+-----------------+                 |
                                    |
                                    v
                          +---------+------------+
                          |                      |
                          |     LLM Service      |
                          |   (llm_service.py)   |
                          |      (Gemini)        |
                          +----------------------+

Technology Stack
Backend: Python, FastAPI, Uvicorn

Browser Automation: Playwright

AI & Natural Language: Google Gemini API

Frontend: React (Vite), Tailwind CSS

Real-time Communication: WebSockets

How It Works
The agent follows a stateful, sequential process to interact with the user and control the browser.

Initiation: The user connects to the frontend, which establishes a WebSocket connection with the FastAPI backend.

Conversation & NLU: The agent asks for the user's name and the purpose of the email. The llm_service.py module, powered by the Gemini API, extracts key details (recipient, subject, primary_reason) from the user's natural language responses.

AI Content Generation: Once all necessary information is gathered, the agent uses the Gemini API (generate_email_body function) to create a professional email body based on the conversation's context.

Browser Automation Trigger: The backend (main.py) calls the browser_controller.py script as a separate process, passing the recipient, subject, and generated body as arguments.

Live Browser Control: The browser_controller.py script, using Playwright:

Launches a real browser instance.

Navigates to gmail.com.

Enters credentials and logs in.

Clicks "Compose", fills in all fields, and clicks "Send".

Visual Feedback Loop:

At each critical step (e.g., after logging in, after composing), the browser controller saves a screenshot to a temporary file.

It then prints a SCREENSHOT::/path/to/image.jpeg message to its standard output.

The main.py backend captures this output, reads the image file, encodes it to Base64, and sends it to the frontend via the WebSocket with type: "image".

Frontend Rendering: The React frontend (App.jsx) receives the WebSocket messages. If a message's type is "image", it renders the Base64 content directly as an image in the chat, providing seamless visual feedback.

Completion: Once the browser script finishes, a final confirmation message is sent to the user, and the agent resets for the next task.

Project Structure
backend/app/

main.py: The FastAPI server, WebSocket logic, and main conversational flow orchestration.

browser_controller.py: A standalone Playwright script that performs all browser interactions.

llm_service.py: Handles all interactions with the Google Gemini API for NLU and text generation.

agent_logic.py: Contains the Pydantic EmailDetails model for managing the conversation's state.

frontend/src/

App.jsx: The main React component that handles the UI, WebSocket connection, and message rendering.

components/: Contains reusable React components like the InputBar.

Setup and Running Instructions
Prerequisites
Python 3.11 (specifically)

Node.js and npm

A test Gmail account (for login credentials)

A Google Gemini API Key

1. Backend Setup
# 1. Navigate to the backend directory
cd backend

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Playwright browsers
playwright install

# 4. Create the environment file
# Create a file named .env in the `backend/` directory and add your credentials:
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
TEST_GMAIL_EMAIL="your_test_email@gmail.com"
TEST_GMAIL_PASSWORD="your_test_password"

# 5. Run the backend server
# This command starts the server and ensures it works correctly on Windows.
python app/main.py

The backend will be running at http://127.0.0.1:8000.

2. Frontend Setup
# 1. Open a new terminal and navigate to the frontend directory
cd frontend

# 2. Install npm packages
npm install

# 3. Run the development server
npm run dev

The frontend will be accessible at http://localhost:5173 (or another port if 5173 is in use). Open this URL in your browser to start interacting with the agent.

Challenges Faced & Solutions
asyncio Event Loop on Windows:

Problem: The initial attempt to run the Playwright subprocess asynchronously using asyncio.create_subprocess_exec failed with a NotImplementedError on Windows.

Solution: The architecture was refactored to use a simpler, more robust subprocess.run() call executed within a separate thread (asyncio.to_thread). This avoids the platform-specific asyncio issue while still preventing the server from blocking.

Real-time Visual Feedback:

Problem: Streaming raw image data directly from the subprocess was complex and prone to errors.

Solution: A file-based approach was implemented. The browser script saves a screenshot and prints its path. The backend then reads this file, encodes it, sends it to the frontend, and deletes the temporary file. This is a highly reliable and platform-agnostic solution.

CORS Errors:

Problem: The frontend was initially blocked from connecting to the backend due to Cross-Origin Resource Sharing (CORS) policies.

Solution: For development, the FastAPI backend was configured to allow all origins (origins = ["*"]). This ensures a smooth development experience. For production, this would be locked down to the specific frontend domain.

Agent in Action
[Screenshot of the chat interface with embedded browser images]