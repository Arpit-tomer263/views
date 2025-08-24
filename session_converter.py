import os
import json
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

async def convert_sessions_to_string_sessions():
    """
    Convert all session files to string sessions, store in accounts.json
    No interactive prompts - simply skips unauthenticated sessions
    """
    print("\n--- Converting .session files to string sessions ---")
    
    # Get all session files
    sessions_dir = "sessions"
    session_files = [file.replace(".session", "") for file in os.listdir(sessions_dir) if file.endswith(".session")]
    
    if not session_files:
        print("No session files found in sessions/ directory")
        return []
    
    print(f"Found {len(session_files)} session files to process")
    
    # Load credentials from database.csv
    phone_credentials = {}
    try:
        with open("database.csv", 'r', encoding='utf-8') as csv_file:
            lines = csv_file.readlines()
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    phone = parts[0].strip("'")
                    phone_credentials[phone] = {
                        'phone': phone,
                        'api_id': int(parts[1]),
                        'api_hash': parts[2]
                    }
    except Exception as e:
        print(f"Error reading database.csv: {e}")
        return []
    
    # Process each session file
    authorized_accounts = []
    skipped = []
    
    for phone in session_files:
        try:
            # Get credentials for this phone
            creds = phone_credentials.get(phone)
            if not creds:
                print(f"No credentials found for {phone}, skipping")
                skipped.append(phone)
                continue
            
            # Create client with session file
            client = TelegramClient(f"sessions/{phone}", creds['api_id'], creds['api_hash'])
            await client.connect()
            
            # Check if authorized without prompting
            if not await client.is_user_authorized():
                print(f"Session {phone} is not authenticated, skipping")
                skipped.append(phone)
                await client.disconnect()
                continue
            
            # Get string session
            string_session = StringSession.save(client.session)
            
            # Store account info
            account = {
                'phone': phone,
                'api_id': creds['api_id'],
                'api_hash': creds['api_hash'],
                'string_session': string_session
            }
            
            authorized_accounts.append(account)
            print(f"✅ Successfully converted {phone} to string session")
            
            # Disconnect client
            await client.disconnect()
            
        except Exception as e:
            print(f"❌ Error converting {phone}: {e}")
            skipped.append(phone)
    
    # Save to accounts.json
    if authorized_accounts:
        with open("accounts.json", 'w') as f:
            json.dump(authorized_accounts, f, indent=4)
        print(f"✅ Saved {len(authorized_accounts)} string sessions to accounts.json")
    else:
        print("❌ No authenticated sessions found to convert")
    
    print(f"Summary: Converted {len(authorized_accounts)} sessions, skipped {len(skipped)} sessions")
    return authorized_accounts

# Run as a standalone script
if __name__ == "__main__":
    asyncio.run(convert_sessions_to_string_sessions())
