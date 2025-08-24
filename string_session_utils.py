import json
import random
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetMessagesViewsRequest, ImportChatInviteRequest
from telethon.tl.types import InputPeerChannel
import asyncio
async def load_string_sessions():
    """Load string sessions from accounts.json"""
    try:
        with open("accounts.json", "r") as f:
            accounts = json.load(f)
        return accounts
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading accounts.json: {e}")
        return []

# Add this to your string_session_utils.py
async def join_channel_with_string_session(account, channel_id, channel_link=None):
    """Join channel with proper entity resolution"""
    from telethon import TelegramClient
    from telethon.tl.functions.channels import JoinChannelRequest, GetFullChannelRequest
    from telethon.tl.functions.messages import ImportChatInviteRequest
    from telethon.errors import FloodWaitError, UserAlreadyParticipantError
    import asyncio
    
    try:
        client = TelegramClient(
            StringSession(account['string_session']),
            account['api_id'],
            account['api_hash']
        )
        
        await client.connect()
        
        if not await client.is_user_authorized():
            print(f"Session {account['phone']} is not authenticated")
            return False, None
        
        # Try multiple ways to resolve the entity
        channel_entity = None
        
        # Method 1: Try with channel ID directly
        try:
            channel_entity = await client.get_entity(int(channel_id))
            print(f"Resolved entity using direct ID for {account['phone']}")
        except Exception as e1:
            print(f"Direct ID resolution failed: {e1}")
            
            # Method 2: Try with channel link if available
            if channel_link:
                try:
                    if channel_link.startswith('https://t.me/'):
                        username = channel_link.replace('https://t.me/', '').replace('+', '')
                        channel_entity = await client.get_entity(username)
                        print(f"Resolved entity using link for {account['phone']}")
                except Exception as e2:
                    print(f"Link resolution failed: {e2}")
                    
                    # Method 3: Try importing invite link
                    if '+' in channel_link:
                        try:
                            hash_part = channel_link.split('+')[-1]
                            result = await client(ImportChatInviteRequest(hash_part))
                            channel_entity = result.chats[0]
                            print(f"Resolved entity using invite for {account['phone']}")
                        except Exception as e3:
                            print(f"Invite resolution failed: {e3}")
        
        if not channel_entity:
            await client.disconnect()
            return False, None
        
        # Try to join the channel
        try:
            await client(JoinChannelRequest(channel_entity))
            print(f"Joined channel successfully for {account['phone']}")
        except UserAlreadyParticipantError:
            print(f"Already a member for {account['phone']}")
        except Exception as join_error:
            print(f"Join error for {account['phone']}: {join_error}")
        
        await client.disconnect()
        return True, channel_entity
        
    except Exception as e:
        print(f"Error in join_channel_with_string_session for {account['phone']}: {e}")
        try:
            await client.disconnect()
        except:
            pass
        return False, None
async def validate_and_filter_sessions():
    """Remove invalid sessions from the pool - FIXED VERSION"""
    from string_session_utils import load_string_sessions
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    import json
    import traceback
    
    print("Loading existing sessions...")
    accounts = await load_string_sessions()
    if not accounts:
        print("No accounts found to validate")
        return []
    
    valid_accounts = []
    
    for i, account in enumerate(accounts):
        try:
            print(f"Validating session {i+1}/{len(accounts)}: {account['phone']}")
            
            # Create client
            client = TelegramClient(
                StringSession(account['string_session']),
                account['api_id'],
                account['api_hash']
            )
            
            # Connect with timeout
            await asyncio.wait_for(client.connect(), timeout=10.0)
            
            # Check authentication with timeout
            is_authorized = await asyncio.wait_for(client.is_user_authorized(), timeout=5.0)
            
            if is_authorized:
                valid_accounts.append(account)
                print(f"✅ Session {account['phone']} is valid")
            else:
                print(f"⚠️  Session {account['phone']} is not authenticated - keeping anyway (might need 2FA)")
                # Keep unauthenticated sessions - they might just need 2FA
                valid_accounts.append(account)
            
            await client.disconnect()
            
        except asyncio.TimeoutError:
            print(f"⚠️  Session {account['phone']} timed out - keeping anyway")
            valid_accounts.append(account)  # Keep sessions that timeout
        except Exception as e:
            error_str = str(e).upper()
            print(f"Error validating {account['phone']}: {e}")
            
            # Only remove sessions with critical errors
            if any(critical_error in error_str for critical_error in [
                "INVALID SESSION", 
                "SESSION_REVOKED", 
                "AUTH_KEY_DUPLICATED",
                "PHONE_NUMBER_INVALID"
            ]):
                print(f"❌ Session {account['phone']} has critical error - removing")
            else:
                print(f"⚠️  Session {account['phone']} has non-critical error - keeping")
                valid_accounts.append(account)
            
            try:
                await client.disconnect()
            except:
                pass
        
        # Add delay between session checks
        await asyncio.sleep(0.5)
    
    # Only save if we have valid accounts, otherwise keep original
    if valid_accounts:
        print(f"Saving {len(valid_accounts)} sessions (was {len(accounts)})")
        
        # Backup original file first
        try:
            with open('accounts.json', 'r') as f:
                original_data = f.read()
            with open('accounts.json.backup', 'w') as f:
                f.write(original_data)
            print("Created backup of original accounts.json")
        except Exception as e:
            print(f"Could not create backup: {e}")
        
        # Save valid accounts
        with open('accounts.json', 'w') as f:
            json.dump(valid_accounts, f, indent=2)
    else:
        print("⚠️  No valid sessions found - keeping original accounts.json")
    
    return valid_accounts


async def increment_view_with_string_session(account, msg_id, channel_entity):
    """
    Increment view for a message using string session
    Returns: True if successful, False otherwise
    """
    client = None
    try:
        client = TelegramClient(
            StringSession(account['string_session']), 
            account['api_id'], 
            account['api_hash']
        )
        
        await client.connect()
        
        if not await client.is_user_authorized():
            print(f"Session {account['phone']} is not authenticated")
            return False
        
        # Create channel peer
        channel_peer = InputPeerChannel(
            channel_id=channel_entity.id,
            access_hash=channel_entity.access_hash
        )
        
        # Increment views
        msg_id_int = int(msg_id)
        await client(GetMessagesViewsRequest(
            peer=channel_peer,
            id=[msg_id_int],
            increment=True
        ))
        
        # Get current view count for monitoring
        messages = await client.get_messages(channel_entity.id, ids=[msg_id_int])
        if messages and messages[0]:
            current_views = messages[0].views
            print(f"Current view count for message {msg_id_int}: {current_views}")
        
        return True
    except Exception as e:
        print(f"Error processing view with {account['phone']}: {e}")
        return False
    finally:
        if client:
            await client.disconnect()

async def get_last_message_with_string_session(account, channel_id):
    """
    Get the last message ID from a channel using string session
    Returns: message_id or None
    """
    client = None
    try:
        client = TelegramClient(
            StringSession(account['string_session']), 
            account['api_id'], 
            account['api_hash']
        )
        
        await client.connect()
        
        if not await client.is_user_authorized():
            print(f"Session {account['phone']} is not authenticated")
            return None
        
        # Get last message
        messages = await client.get_messages(int(channel_id), limit=1)
        
        if messages and len(messages) > 0:
            return messages[0].id
        
        return None
    except Exception as e:
        print(f"Error getting last message with {account['phone']}: {e}")
        return None
    finally:
        if client:
            await client.disconnect()

# Helper function to get random accounts
def get_random_accounts(accounts, count=1):
    """Get random accounts from the list"""
    if not accounts:
        return []
    
    return random.sample(accounts, min(count, len(accounts)))
