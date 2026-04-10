#!/usr/bin/env python3
"""
Check available models for Google Gemini API
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

def check_available_models():
    """Check what models are available"""
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Please set GOOGLE_API_KEY in your .env file")
        return
    
    genai.configure(api_key=api_key)
    
    print("=== Available Models ===")
    try:
        models = genai.list_models()
        for model in models:
            print(f"Model: {model.name}")
            print(f"  Display Name: {model.display_name}")
            print(f"  Description: {model.description}")
            print(f"  Supported Methods: {model.supported_generation_methods}")
            print("-" * 50)
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    check_available_models()
