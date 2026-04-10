#!/usr/bin/env python3
"""
Interactive Chat with PinBot

Run this to ask questions directly to your AI agent.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.agent_with_persona import AgentWithPersona
from dotenv import load_dotenv

def main():
    print(" PinBot - Generic AI Assistant")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    
    # Initialize agent
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print(" Please set GOOGLE_API_KEY in your .env file")
        return
    
    agent = AgentWithPersona(google_api_key=api_key)
    
    # Set persona
    agent.set_persona("General Assistant")
    print(f"Persona: {agent.get_welcome_message()}")
    
    # Ingest documents
    print("\n Loading documents...")
    result = agent.ingest_from_uploads()
    if result['status'] == 'success':
        print(f" Loaded {result['documents_processed']} documents")
        print(f" Created {result['chunks_created']} knowledge chunks")
        print(f"✅ Created {result['chunks_created']} knowledge chunks")
    else:
        print(f"❌ Error loading documents: {result.get('error')}")
    
    print("\n💬 Chat with PinBot (type 'quit' to exit)")
    # Show current usage
    agent_stats = agent.get_agent_stats()
    usage_stats = agent_stats.get('rag_pipeline_stats', {}).get('free_tier_usage', {})
    daily_usage = usage_stats.get('daily', {}).get('gemini-2.5-flash', {})
    print(f"\nToday's Usage: {daily_usage.get('used', 0)}/{daily_usage.get('limit', 20)} requests")
    print(f"Remaining: {daily_usage.get('remaining', 20)} requests")
    
    print("\n" + "-" * 50)
    
    # Chat loop
    while True:
        try:
            question = input("\n🏠 You: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if question.lower() in ['usage', 'stats', 'limit']:
                agent_stats = agent.get_agent_stats()
                usage_stats = agent_stats.get('rag_pipeline_stats', {}).get('free_tier_usage', {})
                daily = usage_stats.get('daily', {}).get('gemini-2.5-flash', {})
                minute = usage_stats.get('minute', {}).get('gemini-2.5-flash', {})
                
                print(f"\n=== Usage Statistics ===")
                print(f"Daily: {daily.get('used', 0)}/{daily.get('limit', 20)} requests")
                print(f"Remaining today: {daily.get('remaining', 20)} requests")
                print(f"Per minute: {minute.get('used', 0)}/{minute.get('limit', 15)} requests")
                print(f"Available now: {minute.get('remaining', 15)} requests")
                continue
            
            if not question:
                continue
            
            print("🤔 PinBot is thinking...")
            
            # Get response
            response = agent.query_with_persona(question)
            
            print(f"\n🤖 PinBot: {response['answer']}")
            
            # Show sources if available
            if response.get('sources'):
                print(f"\n📚 Sources: {len(response['sources'])} documents used")
                for i, source in enumerate(response['sources'][:2], 1):
                    print(f"   {i}. {source['content'][:100]}...")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
