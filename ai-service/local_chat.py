#!/usr/bin/env python3
"""
Local chat simulation for testing without API calls
"""

import os
import sys
from pathlib import Path
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
    agent.set_persona("General Assistant")
    print(f"Persona: {agent.get_welcome_message()}")
    
    # Show actual uploaded documents
    print("\n=== Available Documents ===")
    uploads_path = Path("Uploads")
    if uploads_path.exists():
        documents = []
        for file_path in uploads_path.glob("*"):
            if file_path.is_file() and file_path.suffix.lower() in {'.pdf', '.txt', '.md'}:
                documents.append(f"Document: {file_path.name}")
        
        if documents:
            for doc in documents:
                print(f"  {doc}")
        else:
            print("  No documents found in Uploads folder")
    else:
        print("  Uploads folder not found")
    
    print("\n=== Chat Simulation ===")
    print("(Type 'quit' to exit)")
    print("Note: This is a simulation - no real API calls made")
    print("-" * 50)
    
    # Enhanced keyword-based responses
    responses = {
        "perfume": "I have the INSPIRED PERFUME 2026 catalog available! It contains information about various fragrances, their notes, prices, and availability.",
        "fragrance": "Based on the perfume catalog, there are various fragrances available with different scent profiles including floral, woody, and citrus notes.",
        "citrus": "Yes, we have citrus perfumes available! The catalog features fresh citrus fragrances with notes of lemon, bergamot, and orange. These are perfect for daytime wear and have a refreshing, energizing scent.",
        "scent": "The catalog includes detailed scent descriptions with top, middle, and base notes for each perfume.",
        "price": "Pricing information is available in the perfume catalog with different sizes and price points for each fragrance.",
        "cost": "The catalog shows various price ranges depending on the perfume size and concentration (EDT, EDP, etc.).",
        "available": "Availability information is in the catalog showing which perfumes are currently in stock.",
        "how many": "The perfume catalog contains multiple fragrance options. For the exact count, please check the catalog details.",
        "notes": "Each perfume has detailed fragrance notes including top, heart (middle), and base notes that create the complete scent profile.",
        "size": "The catalog shows different bottle sizes available for each perfume (30ml, 50ml, 100ml, etc.).",
        "men": "There are perfumes specifically designed for men with masculine scent profiles in the catalog.",
        "women": "The catalog includes feminine fragrances designed specifically for women.",
        "unisex": "Some perfumes in the catalog are unisex and suitable for anyone.",
        "brand": "The catalog includes information about the INSPIRED perfume brand and its collection.",
        "catalog": "The INSPIRED PERFUME 2026 catalog is your main document with all fragrance information.",
        "help": "I can help you find information from the perfume catalog! Ask about fragrances, prices, scents, or availability.",
        "document": "I have access to the INSPIRED PERFUME 2026 catalog with detailed perfume information.",
        "information": "All perfume information is available in the catalog. What specific fragrance details are you looking for?",
        "what": "I can provide information about perfumes from the catalog! Ask about fragrances, prices, scents, or availability!",
        "lemon": "The catalog includes citrus fragrances with lemon notes - bright, fresh, and perfect for summer!",
        "orange": "Orange-based fragrances are available with sweet and zesty citrus notes.",
        "bergamot": "Bergamot scents are featured in several citrus perfumes - elegant and refreshing.",
        "summer": "For summer, citrus perfumes are ideal - light, refreshing, and long-lasting."
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
            response = "I can help you find information from the perfume catalog! Ask about fragrances, prices, scents, availability, or any perfume-related questions. What are you looking for?"
            
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
            if "catalog" in question and any(term in question for term in ["price", "fragrance", "scent"]):
                response += " Would you like more specific details about any particular perfume?"
            elif "how many" in question or "available" in question:
                response += " Are you looking for a specific fragrance or general availability?"
            elif "help" in question or "guid" in question:
                response = "I'm here to help! I can find information about perfumes, fragrances, prices, scents, or availability from the catalog. Just tell me what you need!"
            
            print(f"\nPinBot: {response}")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    local_chat_demo()
