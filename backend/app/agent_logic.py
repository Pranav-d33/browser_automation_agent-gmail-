# backend/app/agent_logic.py
from pydantic import BaseModel, Field
from typing import Optional

class EmailDetails(BaseModel):
    """A Pydantic model to structure the information needed for an email."""
    # User's credentials and name
    user_name: Optional[str] = Field(None, description="The name of the user interacting with the agent.")
    user_email: Optional[str] = Field(None, description="The user's own Gmail address for login.")
    user_password: Optional[str] = Field(None, description="The user's Gmail password for login.")
    
    # Email specific details
    recipient_email: Optional[str] = Field(None, description="The email address of the recipient (e.g., the manager).")
    subject: Optional[str] = Field(None, description="A suitable subject line for the email.")
    primary_reason: Optional[str] = Field(None, description="The main reason for the email, e.g., 'leave application', 'meeting query'.")
    context_details: Optional[str] = Field(None, description="Specific details from the user's request, like dates or topics.")

    def is_ready_for_automation(self):
        """Check if we have all info needed to start the browser automation."""
        return (
            self.user_email and
            self.user_password and
            self.recipient_email and
            self.primary_reason
        )

