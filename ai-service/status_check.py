#!/usr/bin/env python3
"""
Check current status and wait times for API limits
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

def check_status():
    """Check current API status and limits"""
    load_dotenv()
    
    print("=== PinBot Status Check ===")
    
    # Check usage file
    usage_file = Path("usage_tracker.json")
    if usage_file.exists():
        try:
            with open(usage_file, 'r') as f:
                usage_data = json.load(f)
            
            last_reset = datetime.fromisoformat(usage_data["last_reset"])
            print(f"Last reset: {last_reset.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Check gemini-2.5-flash usage
            gemini_2_5_usage = usage_data.get('daily', {}).get('gemini-2.5-flash', 0)
            print(f"gemini-2.5-flash usage: {gemini_2_5_usage}/20 requests")
            
            if gemini_2_5_usage >= 20:
                # Calculate time until reset
                tomorrow = last_reset.date() + timedelta(days=1)
                reset_time = datetime.combine(tomorrow, last_reset.time())
                wait_time = reset_time - datetime.now()
                
                hours = wait_time.seconds // 3600
                minutes = (wait_time.seconds % 3600) // 60
                
                print(f"Status: QUOTA EXCEEDED")
                print(f"Wait time: {hours}h {minutes}m until reset")
                print(f"Reset at: {reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                remaining = 20 - gemini_2_5_usage
                print(f"Status: AVAILABLE")
                print(f"Remaining requests: {remaining}")
                
        except Exception as e:
            print(f"Error reading usage file: {e}")
    else:
        print("No usage data found - fresh start!")
    
    print("\n=== Recommendations ===")
    print("1. Wait for quota reset if exceeded")
    print("2. Use 'usage' command in chat to check status")
    print("3. Consider upgrading to paid plan for higher limits")
    print("4. Try again tomorrow for fresh quota")

if __name__ == "__main__":
    check_status()
