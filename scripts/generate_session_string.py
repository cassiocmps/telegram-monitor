#!/usr/bin/env python3
"""
Interactive helper to generate a Telethon StringSession.
Use this string in your cloud hosting environment (Render, Railway, Fly.io, etc.)
as the TELEGRAM_STRING_SESSION environment variable for zero-disk authentication.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from src.config import api_id, api_hash, phone_number


def main():
    print("=" * 60)
    print("Telethon StringSession Generator for Cloud Hosting")
    print("=" * 60)
    
    target_api_id = api_id or input("Enter Telegram API ID: ").strip()
    target_api_hash = api_hash or input("Enter Telegram API Hash: ").strip()
    target_phone = phone_number or input("Enter phone number (with country code): ").strip()

    print("\nConnecting to Telegram to authorize session...")
    with TelegramClient(StringSession(), target_api_id, target_api_hash) as client:
        session_str = client.session.save()
        me = client.get_me()
        print("\n" + "=" * 60)
        print(f"SUCCESS! Authorized as: {me.first_name} (ID: {me.id})")
        print("=" * 60)
        print("\nCopy the following StringSession and add it to your cloud environment variables:")
        print(f"\nTELEGRAM_STRING_SESSION={session_str}\n")
        print("=" * 60)


if __name__ == "__main__":
    main()

