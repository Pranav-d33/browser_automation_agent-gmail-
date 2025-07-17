# backend/app/agent_logic.py
from pydantic import BaseModel, Field
from typing import Optional

class EmailDetails(BaseModel):
    """A Pydantic model to structure the information needed for an email."""
    user_name: Optional[str] = Field(None, description="The name of the user interacting with the agent.") # <-- ADD THIS LINE
    recipient_email: Optional[str] = Field(None, description="The email address of the recipient.")
    subject: Optional[str] = Field(None, description="A suitable subject line for the email.")
    primary_reason: Optional[str] = Field(None, description="The main reason for the email, e.g., 'leave application', 'meeting query'.")
    context_details: Optional[str] = Field(None, description="Specific details from the user's request, like dates or topics.")

    def is_complete_for_sending(self):
        """Check if we have the minimum required info to send an email."""
        return self.recipient_email and self.subject and self.primary_reason