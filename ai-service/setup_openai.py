#!/usr/bin/env python3
"""
Setup OpenAI integration for better quota
"""

import os
from pathlib import Path

def setup_openai():
    """Setup OpenAI configuration"""
    print("=== OpenAI Integration Setup ===")
    print()
    
    # Check current .env
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
        print("Current .env file:")
        print(content)
        print()
    
    print("=== OpenAI Options ===")
    print("1. Free Tier: ~100 requests/day (gpt-3.5-turbo)")
    print("2. Paid Tier: Thousands requests/day (~$0.002/1K tokens)")
    print("3. Gemini: 20 requests/day (current)")
    print()
    
    print("=== To Add OpenAI ===")
    print("1. Get API key from https://platform.openai.com")
    print("2. Add to .env file:")
    print("   OPENAI_API_KEY=your_openai_key_here")
    print("3. I can modify the code to support both APIs")
    print()
    
    print("=== Recommendation ===")
    print("For testing: OpenAI free tier (5x more requests)")
    print("For production: OpenAI paid tier (unlimited practical use)")
    print()
    
    # Instructions for adding OpenAI
    print("=== Next Steps ===")
    print("1. Get OpenAI API key")
    print("2. I'll update the code to support OpenAI")
    print("3. You can choose which API to use per session")
    print("4. Better quota management")

if __name__ == "__main__":
    setup_openai()
