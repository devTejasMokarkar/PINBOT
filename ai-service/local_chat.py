#!/usr/bin/env python3
"""
Local chat simulation for testing without API calls
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.agent_with_persona import AgentWithPersona
from dotenv import load_dotenv

def local_chat_demo():
    """Demo chat without API calls"""
    print("=== PinBot Local Demo ===")
    print("(This demo works without API calls)")
    
    # Load environment
    load_dotenv()
    
    # Initialize agent
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Please set GOOGLE_API_KEY in your .env file")
        return
    
    agent = AgentWithPersona(google_api_key=api_key)
    
    # Set persona
    agent.set_persona("Real Estate Agent")
    print(f"Persona: {agent.get_welcome_message()}")
    
    # Simulate document loading
    print("\n=== Available Properties ===")
    properties = [
        "Property 1: 2BHK apartment in Bandra - 80L",
        "Property 2: 3BHK villa in Andheri - 1.2Cr", 
        "Property 3: 1BHK studio in Powai - 45L"
    ]
    
    for prop in properties:
        print(f"  {prop}")
    
    print("\n=== Chat Simulation ===")
    print("(Type 'quit' to exit)")
    print("Note: This is a simulation - no real API calls made")
    print("-" * 50)
    
    # Enhanced keyword-based responses
    responses = {
        "2bhk": "I found a great 2BHK apartment in Bandra for 80L. It's spacious and well-located with 2 bedrooms, living room, kitchen, and parking!",
        "3bhk": "There's a beautiful 3BHK villa in Andheri available for 1.2Cr. Perfect for families! It has 3 bedrooms, garden, and 24/7 security.",
        "1bhk": "For budget-conscious buyers, there's a 1BHK studio in Powai for 45L. Cozy and perfect for singles or couples.",
        "apartment": "I have several apartments available. The 2BHK in Bandra (80L) and 1BHK in Powai (45L) are great options!",
        "villa": "The 3BHK villa in Andheri is excellent - 1.2Cr with great amenities like garden, parking, and security!",
        "price": "Properties range from 45L to 1.2Cr. The 1BHK studio is 45L, 2BHK apartment is 80L, and 3BHK villa is 1.2Cr.",
        "location": "Available locations: Bandra (premium area), Andheri (family-friendly), and Powai (budget-friendly).",
        "budget": "What's your budget? I can help find properties: 45L (studio), 80L (2BHK), or 1.2Cr (3BHK villa).",
        "bandra": "Bandra is a premium location! I have a 2BHK apartment there for 80L. Great connectivity and amenities.",
        "andheri": "Andheri is perfect for families! There's a 3BHK villa available for 1.2Cr with excellent facilities.",
        "powai": "Powai offers great value! There's a 1BHK studio for 45L - ideal for first-time buyers.",
        "cheap": "The most affordable option is the 1BHK studio in Powai at 45L. Great for budget-conscious buyers!",
        "expensive": "The premium option is the 3BHK villa in Andheri at 1.2Cr. Luxury living with great amenities!",
        "family": "For families, I recommend the 3BHK villa in Andheri (1.2Cr) - plenty of space and family-friendly neighborhood.",
        "single": "For singles, the 1BHK studio in Powai (45L) is perfect - affordable and low maintenance.",
        "couple": "For couples, the 2BHK apartment in Bandra (80L) offers great space and location!"
    }
    
    while True:
        try:
            question = input("\nYou: ").strip().lower()
            
            if question in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not question:
                continue
            
            # Find best matching response
            response = "I can help you with properties! I have options in Bandra, Andheri, and Powai. What are you looking for specifically?"
            
            # Check for multiple keywords and prioritize
            matched_keywords = []
            for keyword, resp in responses.items():
                if keyword in question:
                    matched_keywords.append((keyword, resp))
            
            if matched_keywords:
                # Use the most specific match (longer keyword)
                matched_keywords.sort(key=lambda x: len(x[0]), reverse=True)
                response = matched_keywords[0][1]
            
            # Add context-aware follow-ups
            if "where" in question and any(loc in question for loc in ["bandra", "andheri", "powai"]):
                response += " Would you like more details about this property?"
            elif "price" in question or "cost" in question or "rate" in question:
                response += " Which price range interests you most?"
            elif "help" in question or "guid" in question:
                response = "I'm here to help! I can show you properties in different budgets and locations. Just tell me what you're looking for!"
            
            print(f"\nPinBot: {response}")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    local_chat_demo()
