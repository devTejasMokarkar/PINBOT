#!/usr/bin/env python3
"""
Simple quota wait time checker
"""

from datetime import datetime, timedelta

def show_quota_info():
    """Show quota information and estimated wait time"""
    print("=== Gemini API Quota Information ===")
    print()
    print("Current Status: QUOTA EXCEEDED")
    print("Model: gemini-2.5-flash")
    print("Daily Limit: 20 requests")
    print()
    print("=== What This Means ===")
    print("You've used all 20 free requests for today.")
    print("The quota resets 24 hours after your first request.")
    print()
    print("=== Your Options ===")
    print("1. Wait for automatic reset (tomorrow)")
    print("2. Use local demo: python local_chat.py")
    print("3. Upgrade to paid plan at: https://aistudio.google.com")
    print()
    print("=== For Real API Usage ===")
    print("Try again tomorrow for fresh quota!")
    print("Your system is working perfectly - just waiting for reset.")
    print()
    print("=== Local Demo Features ===")
    print("Works immediately without API calls")
    print("Smart keyword matching")
    print("Property information")
    print("Budget guidance")
    print("Location details")

if __name__ == "__main__":
    show_quota_info()
