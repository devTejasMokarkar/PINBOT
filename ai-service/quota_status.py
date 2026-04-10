#!/usr/bin/env python3
"""
Check exact quota status and wait times
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

def check_quota_status():
    """Check exact quota status and wait time"""
    load_dotenv()
    
    print("=== PinBot Quota Status ===")
    
    # Check usage file
    usage_file = Path("usage_tracker.json")
    if usage_file.exists():
        try:
            with open(usage_file, 'r') as f:
                usage_data = json.load(f)
            
            last_reset = datetime.fromisoformat(usage_data["last_reset"])
            print(f"Last reset: {last_reset.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Check gemini-2.5-flash usage
            daily_usage = usage_data.get('daily', {}).get('gemini-2.5-flash', 0)
            print(f"gemini-2.5-flash usage: {daily_usage}/20 requests")
            
            if daily_usage >= 20:
                # Calculate exact reset time
                tomorrow = last_reset.date() + timedelta(days=1)
                reset_time = datetime.combine(tomorrow, last_reset.time())
                wait_time = reset_time - datetime.now()
                
                if wait_time.total_seconds() > 0:
                    hours = int(wait_time.total_seconds() // 3600)
                    minutes = int((wait_time.total_seconds() % 3600) // 60)
                    seconds = int(wait_time.total_seconds() % 60)
                    
                    print(f"Status: QUOTA EXCEEDED")
                    print(f"Wait time: {hours}h {minutes}m {seconds}s")
                    print(f"Reset at: {reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Show alternatives
                    print(f"\n=== Alternatives ===")
                    print(f"1. Wait {hours}h {minutes}m for quota reset")
                    print(f"2. Upgrade to paid plan for higher limits")
                    print(f"3. Use tomorrow for fresh quota")
                    print(f"4. Check your Google AI Studio for usage details")
                else:
                    print("Status: QUOTA SHOULD BE RESET - Try now!")
            else:
                remaining = 20 - daily_usage
                print(f"Status: AVAILABLE")
                print(f"Remaining requests: {remaining}")
                
        except Exception as e:
            print(f"Error reading usage file: {e}")
    else:
        print("No usage data found - fresh start!")
    
    print(f"\n=== Free Tier Limits ===")
    print(f"gemini-2.5-flash: 20 requests/day")
    print(f"gemini-embedding-001: 10,000 requests/day")
    print(f"Note: Quota resets 24 hours after first use")

if __name__ == "__main__":
    check_quota_status()
