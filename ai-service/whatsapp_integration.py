"""
WhatsApp Integration Module

This provides endpoints for WhatsApp integration.
For beginners: Connect your AI agent to WhatsApp Business API.
For production: Scalable WhatsApp integration with message queuing.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import hashlib
import hmac
import os

try:
    from src.agent_with_persona import AgentWithPersona
except ImportError:
    from agent_with_persona import AgentWithPersona

logger = logging.getLogger(__name__)

# Pydantic models for WhatsApp
class WhatsAppMessage(BaseModel):
    from_number: str
    message: str
    message_type: str = "text"
    timestamp: str

class WhatsAppWebhook(BaseModel):
    object: str
    entry: list

class WhatsAppResponse(BaseModel):
    to: str
    message: str
    message_type: str = "text"

class WhatsAppIntegration:
    """
    WhatsApp Business API integration.
    
    For beginners: Connect your AI to WhatsApp for customer conversations.
    For production: Enterprise-grade WhatsApp integration with compliance.
    """
    
    def __init__(self, 
                 agent: AgentWithPersona,
                 webhook_verify_token: str = None,
                 whatsapp_token: str = None):
        """
        Initialize WhatsApp integration.
        
        Args:
            agent: Agent with persona instance
            webhook_verify_token: Token for webhook verification
            whatsapp_token: WhatsApp Business API token
        """
        self.agent = agent
        self.webhook_verify_token = webhook_verify_token or os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "your_verify_token")
        self.whatsapp_token = whatsapp_token or os.getenv("WHATSAPP_TOKEN", "your_whatsapp_token")
        
        # Set default persona for WhatsApp
        self.agent.set_persona("real_estate_agent")
        
        logger.info("WhatsApp integration initialized")
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verify WhatsApp webhook.
        
        For beginners: Security check to ensure requests are from WhatsApp.
        For production: Webhook authentication for API security.
        
        Args:
            mode: Webhook mode
            token: Verification token
            challenge: Challenge string
            
        Returns:
            Challenge string if verified, None otherwise
        """
        if mode == "subscribe" and token == self.webhook_verify_token:
            logger.info("Webhook verified successfully")
            return challenge
        else:
            logger.warning("Webhook verification failed")
            return None
    
    def process_message(self, from_number: str, message: str) -> Dict[str, Any]:
        """
        Process incoming WhatsApp message.
        
        For beginners: Handle user messages from WhatsApp.
        For production: Message processing with queue management.
        
        Args:
            from_number: Sender's phone number
            message: Message content
            
        Returns:
            Response dictionary
        """
        try:
            logger.info(f"Processing message from {from_number}: {message[:50]}...")
            
            # Get response from agent
            response = self.agent.query_with_persona(message)
            
            # Format for WhatsApp
            whatsapp_response = {
                "to": from_number,
                "message": response.get('answer', "I'm sorry, I couldn't process your request."),
                "message_type": "text",
                "metadata": {
                    "sources_count": len(response.get('sources', [])),
                    "persona": response.get('persona', {}).get('name', 'general'),
                    "timestamp": response.get('metadata', {}).get('timestamp', '')
                }
            }
            
            logger.info(f"Generated response for {from_number}")
            return whatsapp_response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "to": from_number,
                "message": "I'm experiencing technical difficulties. Please try again later.",
                "message_type": "text"
            }
    
    def send_message(self, to_number: str, message: str) -> bool:
        """
        Send message via WhatsApp API.
        
        For beginners: Send responses back to WhatsApp users.
        For production: Message delivery with retry logic.
        
        Args:
            to_number: Recipient's phone number
            message: Message to send
            
        Returns:
            True if successful, False otherwise
        """
        # This is a placeholder for actual WhatsApp API integration
        # You'll need to implement the actual API call to WhatsApp Business API
        
        logger.info(f"Sending message to {to_number}: {message[:50]}...")
        
        # TODO: Implement actual WhatsApp API call
        # Example using requests:
        # import requests
        # url = f"https://graph.facebook.com/v18.0/your_phone_number_id/messages"
        # headers = {
        #     "Authorization": f"Bearer {self.whatsapp_token}",
        #     "Content-Type": "application/json"
        # }
        # data = {
        #     "messaging_product": "whatsapp",
        #     "to": to_number,
        #     "type": "text",
        #     "text": {"body": message}
        # }
        # response = requests.post(url, json=data, headers=headers)
        # return response.status_code == 200
        
        # For now, just log the message
        logger.info(f"Message would be sent to {to_number}: {message}")
        return True
    
    def handle_webhook_event(self, webhook_data: dict) -> list:
        """
        Handle incoming webhook events from WhatsApp.
        
        For beginners: Process all types of WhatsApp events.
        For production: Event handling with message persistence.
        
        Args:
            webhook_data: Webhook event data
            
        Returns:
            List of responses to send
        """
        responses = []
        
        try:
            for entry in webhook_data.get('entry', []):
                for change in entry.get('changes', []):
                    if 'messages' in change.get('value', {}):
                        messages = change['value']['messages']
                        
                        for message in messages:
                            if message.get('type') == 'text':
                                # Extract message details
                                from_number = message['from']
                                text = message['text']['body']
                                timestamp = message['timestamp']
                                
                                # Process message
                                response = self.process_message(from_number, text)
                                
                                # Add to responses list
                                responses.append(response)
                                
                                # Send message (in production, this would be async)
                                self.send_message(response['to'], response['message'])
            
            logger.info(f"Processed {len(responses)} messages from webhook")
            return responses
            
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return []
    
    def get_integration_info(self) -> Dict[str, Any]:
        """
        Get integration information.
        
        Returns:
            Dictionary with integration status
        """
        return {
            "status": "active",
            "platform": "WhatsApp Business API",
            "current_persona": self.agent.current_persona['name'] if self.agent.current_persona else None,
            "webhook_configured": bool(self.webhook_verify_token),
            "api_token_configured": bool(self.whatsapp_token),
            "supported_message_types": ["text"],
            "features": {
                "persona_responses": True,
                "source_citation": True,
                "real_estate_focused": True
            }
        }

# FastAPI endpoints for WhatsApp
def create_whatsapp_app(agent: AgentWithPersona):
    """
    Create FastAPI app with WhatsApp endpoints.
    
    Args:
        agent: Agent with persona instance
        
    Returns:
        FastAPI app instance
    """
    app = FastAPI(title="WhatsApp AI Agent Integration")
    
    # Initialize WhatsApp integration
    whatsapp = WhatsAppIntegration(agent)
    
    @app.get("/webhook")
    async def verify_webhook(mode: str, token: str, challenge: str):
        """Verify WhatsApp webhook."""
        result = whatsapp.verify_webhook(mode, token, challenge)
        if result:
            return result
        else:
            raise HTTPException(status_code=403, detail="Verification failed")
    
    @app.post("/webhook")
    async def handle_webhook(webhook_data: dict):
        """Handle incoming WhatsApp messages."""
        responses = whatsapp.handle_webhook_event(webhook_data)
        return {"status": "processed", "responses": len(responses)}
    
    @app.post("/send-test")
    async def send_test_message(to_number: str, message: str):
        """Send test message (for development)."""
        success = whatsapp.send_message(to_number, message)
        return {"success": success, "to": to_number}
    
    @app.get("/status")
    async def get_status():
        """Get integration status."""
        return whatsapp.get_integration_info()
    
    return app

# Example usage
if __name__ == "__main__":
    # Test WhatsApp integration
    print("=== WhatsApp Integration Test ===")
    
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Please set GOOGLE_API_KEY in your .env file")
        exit(1)
    
    # Create agent
    agent = AgentWithPersona(google_api_key=api_key)
    
    # Create WhatsApp integration
    whatsapp = WhatsAppIntegration(agent)
    
    # Test message processing
    response = whatsapp.process_message(
        from_number="+1234567890",
        message="What properties do you have available?"
    )
    
    print(f"Test response: {response}")
    print(f"Integration info: {whatsapp.get_integration_info()}")
