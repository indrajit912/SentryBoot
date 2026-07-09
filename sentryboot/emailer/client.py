import requests
from typing import List, Union, Optional

class HermesClient:
    """Hermes Email API Client.
    
    Reuses the integration pattern from the ExpenseWise application.
    """
    def __init__(self, base_url: str, api_key: str, bot_id: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.bot_id = bot_id

    def send_email(self, 
                   to_emails: Union[str, List[str]], 
                   subject: str, 
                   body_html: Optional[str] = None, 
                   from_name: str = "SentryBoot") -> dict:
        """Sends an email using the Hermes `/api/v1/send-email` API endpoint.
        
        Args:
            to_emails: Recipient email address(es)
            subject: Email subject line
            body_html: Optional HTML formatted body
            from_name: Name of the sender (defaults to 'SentryBoot')
            
        Returns:
            dict: The JSON response from the Hermes API
        """
        endpoint = f"{self.base_url}/api/v1/send-email"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        to_list = to_emails if isinstance(to_emails, list) else [to_emails]
        
        payload = {
            "to": to_list,
            "subject": subject,
            "from_name": from_name
        }
        
        if self.bot_id:
            payload["bot_id"] = self.bot_id
        if body_html:
            payload["email_html_text"] = body_html
            
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Raise exception so calling modules can handle logging and console feedback
            raise RuntimeError(f"Hermes email API call failed: {str(e)}") from e
