#!/usr/bin/env python3
"""
Call Management CLI - Terminate and manage calls via command line
"""

import sys
import requests
import argparse

def terminate_call(call_id):
    """Terminate a specific call"""
    try:
        response = requests.post(f"http://localhost:5000/api/calls/{call_id}/terminate", timeout=10)
        if response.status_code == 200:
            print(f"✅ Call {call_id} terminated successfully")
        else:
            print(f"❌ Failed to terminate call: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def cleanup_calls():
    """Clean up stuck calls"""
    try:
        response = requests.post("http://localhost:5000/api/calls/cleanup", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['message']}")
        else:
            print(f"❌ Cleanup failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def list_active_calls():
    """List active calls"""
    try:
        response = requests.get("http://localhost:5000/api/calls", timeout=10)
        if response.status_code == 200:
            result = response.json()
            active_calls = [call for call in result['calls'] if call['status'] in ['in_progress', 'dialing']]
            
            if active_calls:
                print(f"\n📞 Active Calls ({len(active_calls)}):")
                print("-" * 50)
                for call in active_calls:
                    print(f"ID: {call['id'][:8]}... | Status: {call['status']} | Caller: {call['caller_name']} | To: {call['phone_number']}")
            else:
                print("✅ No active calls")
        else:
            print(f"❌ Failed to get calls: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    parser = argparse.ArgumentParser(description='Call Management CLI')
    parser.add_argument('action', choices=['terminate', 'cleanup', 'list'], help='Action to perform')
    parser.add_argument('--call-id', help='Call ID to terminate (required for terminate action)')
    
    args = parser.parse_args()
    
    if args.action == 'terminate':
        if not args.call_id:
            print("❌ --call-id is required for terminate action")
            sys.exit(1)
        terminate_call(args.call_id)
    elif args.action == 'cleanup':
        cleanup_calls()
    elif args.action == 'list':
        list_active_calls()

if __name__ == '__main__':
    main()
