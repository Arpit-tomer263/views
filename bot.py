async def join_all_sessions_to_channel():
    """Join all session IDs to the Helping_channel_link channel before starting the bot."""
    import config
    # Use getattr so missing constants in config.py don't raise ImportError
    Helping_channel_link = getattr(config, 'Helping_channel_link', None)
    Helping_channel_id = getattr(config, 'Helping_channel_id', None)
    
    if not Helping_channel_link or not Helping_channel_id:
        print("ERROR: Missing Helping_channel_link or Helping_channel_id in config.py")
        print("Please add these values to your config.py file")
        return
        
    sessions_dir = "sessions"
    session_files = [file.replace(".session", "") for file in os.listdir(sessions_dir) if file.endswith(".session")]
    joined = []
    already_joined = []
    failed = []
    print("\n--- Joining all session IDs to the helping channel ---")
    for phone in session_files:
        try:
            # Load credentials from database.csv
            with open("database.csv", 'r', encoding='utf-8') as csv_file:
                lines = csv_file.readlines()
                creds = None
                for line in lines:
                    if phone in line:
                        parts = line.split(',')
                        if len(parts) >= 3:
                            creds = {
                                'phone': parts[0].strip("'"),
                                'app_id': int(parts[1]),
                                'api_hash': parts[2]
                            }
                        break
            if not creds:
                print(f"No credentials found for {phone}")
                failed.append(phone)
                continue
            client = TelegramClient(f"sessions/{phone}", creds['app_id'], creds['api_hash'])
            await client.connect()
            if not await client.is_user_authorized():
                print(f"Session {phone} is not authenticated, skipping")
                failed.append(phone)
                await client.disconnect()
                continue
            # Check if already joined
            try:
                await client.get_entity(int(Helping_channel_id))
                print(f"{phone} is already joined")
                already_joined.append(phone)
            except Exception:
                # Try to join using invite link
                try:
                    await client(ImportChatInviteRequest(Helping_channel_link.split('/')[-1]))
                    print(f"{phone} joined the channel")
                    joined.append(phone)
                except Exception as join_err:
                    print(f"{phone} failed to join: {join_err}")
                    failed.append(phone)
            await client.disconnect()
        except Exception as e:
            print(f"Error with {phone}: {e}")
            failed.append(phone)
    print("\n--- Join Summary ---")
    print(f"Already joined: {already_joined}")
    print(f"Joined: {joined}")
    print(f"Failed: {failed}")
from telegram import Update,InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, filters,ApplicationBuilder,ContextTypes
from telethon.tl.functions.messages import GetMessagesViewsRequest
import random
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import InputPeerChannel
from telethon.sessions import StringSession
from telethon import TelegramClient, errors
from config import TOKEN,Database,Helping_channel_id
import json
import threading
import asyncio
import os
import time
import concurrent.futures
import multiprocessing
from queue import Queue
from functools import partial
# Bot Commands


# Helper Command
async def get_channel_name(channel_id: str, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Fetches the channel name from its ID."""
    try:
        chat = await context.bot.get_chat(channel_id)
        return chat.title  # Channel name
    except Exception as e:
        return f"Error: {e}"

account_details = [
                    ('+916380126013', 27539035, 'bd672675fdc17d41f67c59b164600694', "sessions/+916380126013.session"),
                    ('+916381117615', 26220461, 'dc28d77880ae5718f5d9ceddae0dee07', "sessions/+916381117615.session"),
                    ('+916382949650', 27559355, 'b3207c5de89f5dafbf18289eac33963b', "sessions/+916382949650.session"),
                    ('+916385809749', 26306541, '965649c89fdfc9c79999758e94c4d584', "sessions/+916385809749.session"),
                    ('+916386254734', 25782502, '0535db4f82c2e670f115ba9b03d1ecfa', "sessions/+916386254734.session"),
                    ('+916386568277', 28859253, '146acdfc7a4ec659e603023f38de8106', "sessions/+916386568277.session"),
                    ('+916387050619', 29701789, '13d8f62b6efe1a5b490cf3de45fee273', "sessions/+916387050619.session"),
                    ('+916387193358', 28185176, '0b435667ab227af7e4116a770582e0b1', "sessions/+916387193358.session"),
                    ('+916387485515', 27595658, '97d8e3746374ddfca988ce8ace6add48', "sessions/+916387485515.session"),
                    ('+918403967443', 22353806, '34ac8a6de736fb332b38aeefcef86b6b', "sessions/+918403967443.session"),
                    ('+916394905700', 24939296, '6634bf834a615b209c341708f7703c64', "sessions/+916394905700.session"),
                    ('+918688040363', 21011567, '2abe4727c4c3f4f5b87a10a7dc795f4a', "sessions/+918688040363.session"),
                    ('+919085977354', 24126316, 'f3c46e86db46a50f797fe6fdf1fd2f44', "sessions/+919085977354.session"),
                    ('+917429384114', 22310386, '92645f8cb62565c39c36cbad402b43e0', "sessions/+917429384114.session"),
                    ('+916387410489', 29670218, '43dd43bdb6fcbb63d5e0b8ffb7831386', "sessions/+916387410489.session"),
                    ('+916387839619', 21788185, '7e0b801c8feef62c36c07feb77c407c4', "sessions/+916387839619.session"),
                    ('+916392463191', 25781341, '31a1688e18eefa0b83e229a3de3cefd2', "sessions/+916392463191.session"),
                    ('+916395372893', 20910738, 'dfc0fd0cf0b2c47c48d62a16f8cf19c9', "sessions/+916395372893.session"),
                    ('+917398619905', 22004285, '190b58a9f23be201e50f00881ea2b27c', "sessions/+917398619905.session"),
                    ('+917411945327', 23604891, 'a1f84391d78597941501c18b3916caf9', "sessions/+917411945327.session"),
                    ('+917415362431', 24539220, '1bbcc32806228c7240e40b3c596ecfa4', "sessions/+917415362431.session"),
                    ('+917415403570', 23231291, '93ec05bf79ff0fafcaa347ac68e36ced', "sessions/+917415403570.session"),
                    ('+917416604452', 23928654, '3af82656aca732bf7dc6570e42013bec', "sessions/+917416604452.session"),
                    ('+917416605302', 25755850, '889dca1897fd38512a7446a3261c81fe', "sessions/+917416605302.session"),
                    ('+917417784097', 28402991, '815f990789263eea04f722d7ac609280', "sessions/+917417784097.session")
                ]

converted = []

for phone, api_id, api_hash, session_file in account_details:
    try:
        client = TelegramClient(session_file, api_id, api_hash)
        client.connect()

        if not client.is_user_authorized():
            print(f"⚠️ Skipping {phone}: Not authorized")
            client.disconnect()
            continue

        string_session = StringSession.save(client.session)
        converted.append({
            "phone": phone,
            "api_id": api_id,
            "api_hash": api_hash,
            "string_session": string_session
        })
        print(f"✅ Converted {phone}")

        client.disconnect()
    except Exception as e:
        print(f"❌ Failed {phone}: {e}")

if converted:
    with open("accounts.json", "w") as f:
        json.dump(converted, f, indent=4)
    print("All authorized sessions saved to accounts.json")
else:
    print("⚠️ No authorized accounts were converted.")

# /start --> Command
async def start(update:Update,context:CallbackContext):
    await update.message.reply_text("Welcome to the Views Increaser Bot!")

# help --> help
async def help_command(update: Update, context: CallbackContext):
    message = """
<b>📌 Bot Help Menu</b>

✨ <i>Available Commands:</i>

1️⃣ <b>/increase_views</b> – Set the per-minute views you want.
2️⃣ <b>/set_target</b> – Set the total target views on that channel post.
3️⃣ <b>/variation</b> – Set the variation in views.
4️⃣ <b>/add_channel</b> – Add a channel to the list.

💡 <i>Tip: Use these commands to control and customize your view settings easily!</i>
"""
    await update.message.reply_text(message.strip(), parse_mode="HTML")

# /add_channel
async def add_channel(update: Update, context: CallbackContext):
    await update.message.reply_text("Please send me the channel ID to add. But before sending The ID please add this bot in the channel and make that bot admin.")
    context.user_data['adding_channel'] = True

# /variation
async def variation(update: Update, context: CallbackContext):
    buttons = []
    with open(Database, 'r') as db_file:
        data = json.load(db_file)
        for idx, data in data.items():
            name = await get_channel_name(idx, context)
            buttons.append([InlineKeyboardButton(text=name, callback_data=f"set_variation_{idx}")])
    await update.message.reply_text("Choose the channel.", reply_markup=InlineKeyboardMarkup(buttons))

# set_target
async def set_target(update:Update,context:CallbackContext):
    buttons = []
    with open(Database, 'r') as db_file:
        data = json.load(db_file)
        for idx, data in data.items():
            name = await get_channel_name(idx, context)
            buttons.append([InlineKeyboardButton(text=name, callback_data=f"set_target_{idx}")])
    await update.message.reply_text("Choose the channel.", reply_markup=InlineKeyboardMarkup(buttons))

# increase_views
async def increase_views(update: Update, context: CallbackContext):
    buttons = []
    with open(Database, 'r') as db_file:
        data = json.load(db_file)
        for idx, data in data.items():
            name = await get_channel_name(idx, context)
            buttons.append([InlineKeyboardButton(text=name, callback_data=f"increase_views_{idx}")])
    await update.message.reply_text("Choose the channel.", reply_markup=InlineKeyboardMarkup(buttons))

async def Message_handler(update: Update, context: CallbackContext):
    if context.user_data.get('adding_channel'):
        channel_id = update.message.text
        await update.message.reply_text(f"Channel ID {channel_id} added successfully!")
        context.user_data['adding_channel'] = False
        with open(Database, 'r') as db_file:
            data = json.load(db_file)
        data[channel_id] = {
            'views_per_minute': 0,
            'target_views': 0,
            'variation': 0,
            'msg_ids':{}
        }
        with open(Database, 'w') as db_file:
            json.dump(data, db_file)
        context.user_data['adding_channel'] = False
        
    elif context.user_data.get('setting_variation'):
        variation = update.message.text
        if variation.isdigit():
            variation = int(variation)
            channel_id = context.user_data.get('current_channel')
            with open(Database, 'r') as db_file:
                data = json.load(db_file)
            if channel_id in data:
                data[channel_id]['variation'] = variation
                with open(Database, 'w') as db_file:
                    json.dump(data, db_file)
                await update.message.reply_text(f"Variation for channel {channel_id} set to {variation}%.")
            else:
                await update.message.reply_text("Channel not found.")
        else:
            await update.message.reply_text("Please send a valid number.")
        context.user_data['setting_variation'] = False

    elif context.user_data.get('setting_target'):
        target = update.message.text
        if target.isdigit():
            target = int(target)
            channel_id = context.user_data.get('current_channel')
            with open(Database, 'r') as db_file:
                data = json.load(db_file)
            if channel_id in data:
                data[channel_id]['target_views'] = target
                with open(Database, 'w') as db_file:
                    json.dump(data, db_file)
                await update.message.reply_text(f"Target views for channel {channel_id} set to {target}.")
            else:
                await update.message.reply_text("Channel not found.")
        else:
            await update.message.reply_text("Please send a valid number.")
        context.user_data['setting_target'] = False

    elif context.user_data.get('increasing_views'):
        views = update.message.text
        if views.isdigit():
            views = int(views)
            channel_id = context.user_data.get('current_channel')
            with open(Database, 'r') as db_file:
                data = json.load(db_file)
            if channel_id in data:
                data[channel_id]['views_per_minute'] = views
                with open(Database, 'w') as db_file:
                    json.dump(data, db_file)
                await update.message.reply_text(f"Views per minute for channel {channel_id} set to {views}.")
            else:
                await update.message.reply_text("Channel not found.")
        else:
            await update.message.reply_text("Please send a valid number.")
        context.user_data['increasing_views'] = False

async def Button_handler(update:Update,context:CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("set_variation_"):
        channel_id = data.split("_")[-1]
        context.user_data['current_channel'] = channel_id
        await query.message.reply_text("Please send me the variation in Percent Only numbers.")
        context.user_data['setting_variation'] = True

    elif data.startswith("set_target_"):
        channel_id = data.split("_")[-1]
        context.user_data['current_channel'] = channel_id
        await query.message.reply_text("Please send me the target views in Only numbers.")
        context.user_data['setting_target'] = True

    elif data.startswith("increase_views_"):
        channel_id = data.split("_")[-1]
        context.user_data['current_channel'] = channel_id
        await query.message.reply_text("Please send me the number of views that you want in one minute Only numbers.")
        context.user_data['increasing_views'] = True


def get_telethon_channel_id(channel_id):
    """
    Convert a regular Telegram channel ID to the format expected by Telethon.
    Telethon expects channel IDs without the -100 prefix.
    """
    channel_id = str(channel_id)
    if channel_id.startswith('-100'):
        return int(channel_id[4:])
    elif channel_id.startswith('-'):
        return int(channel_id[1:])
    return int(channel_id)


async def Manage_postes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    import random, json, os
    from telethon import TelegramClient
    from telethon.sessions import StringSession

    print("new Post")
    if not update.channel_post:
        print("Returning......")
        return

    data = {}
    channel_id = update.channel_post.chat.id
    message_id = update.channel_post.message_id

    try:
        with open(Database, 'r') as db_file:
            data = json.load(db_file)

        if str(channel_id) in data:
            channel_data = data[str(channel_id)]
            views_per_minute = channel_data.get('views_per_minute', 0)
            target_views = channel_data.get('target_views', 0)
            variation = channel_data.get('variation', 0)

            print(f"Channel ID: {channel_id}, Message ID: {message_id}, Views per minute: {views_per_minute}, Target views: {target_views}, Variation: {variation}")

            if target_views > 0 and variation > 0:
                if Helping_channel_id:
                    await context.bot.forward_message(
                        chat_id=Helping_channel_id,
                        from_chat_id=channel_id,
                        message_id=message_id
                    )

                a = round((target_views * variation) / 100)
                max_view = target_views + a if random.choice([True, False]) else target_views - a

                if views_per_minute > 0:
                    remainder = max_view % views_per_minute
                    if remainder != 0:
                        max_view -= remainder

                max_view = int(max_view)

                # 🔹 Load accounts from JSON with StringSessions
                with open("accounts.json", "r") as f:
                    account_details = json.load(f)

                random.shuffle(account_details)
                success = False

                for acc in account_details:
                    phone = acc["phone"]
                    aid = acc["api_id"]
                    hid = acc["api_hash"]
                    ssession = acc["string_session"]

                    client = TelegramClient(StringSession(ssession), aid, hid)
                    try:
                        await client.start()
                        if not await client.is_user_authorized():
                            print(f"User {phone} is not authorized")
                            continue

                        try:
                            last_msg = await client.get_messages(int(Helping_channel_id), limit=1)
                            if last_msg and len(last_msg) > 0:
                                fetched_id = last_msg[0].id   # ✅ take first message

                                print(f"✅ Message ID got: {fetched_id}")
                                channel_data['msg_ids'][str(fetched_id)] = max_view

                                temp_file = f"{Database}.tmp"
                                with open(temp_file, 'w') as db_file:
                                    json.dump(data, db_file)
                                os.replace(temp_file, Database)

                                print(f"Forwarding post from {channel_id} with settings: {views_per_minute}, {target_views}, {variation}")
                                print(f"Message ID {fetched_id} stored with max_view: {max_view}")
                                success = True
                                break
                            else:
                                print("❌ Unable to fetch Message ID")
                        except Exception as e:
                            print(f"❌ Error fetching message from {phone}: {e}")

                    except Exception as e:
                        print(f"❌ Error with {phone}: {e}")
                    finally:
                        await client.disconnect()

                if not success:
                    try:
                        await context.bot.send_message(chat_id=5856117513, text=f"Unable to store message ID for channel {channel_id}")
                    except Exception as notify_err:
                        print(f"Failed to notify admin: {notify_err}")

        else:
            print(f"Channel ID {channel_id} not found in database.")
    except Exception as e:
        print(f"Error in Manage_postes: {e}")

async def process_view(phone, msg_id, channel_id, Helping_channel_id):
    """Process a single view with the given phone number session"""
    # Load credentials from database.csv
    try:
        with open("database.csv", 'r', encoding='utf-8') as csv_file:
            lines = csv_file.readlines()

            # Find credentials for this phone number
            creds = None
            for line in lines:
                if phone in line:
                    parts = line.split(',')
                    if len(parts) >= 3:
                        creds = {
                            'phone': parts[0].strip("'"),
                            'app_id': int(parts[1]),
                            'api_hash': parts[2]
                        }
                    break
    except Exception as e:
        print(f"Error reading credentials for {phone}: {e}")
        return None
    
    if not creds:
        print(f"No credentials found for {phone}")
        return None
    
    # Create client and process view
    client = None
    try:
        client = TelegramClient(f"sessions/{phone}", creds['app_id'], creds['api_hash'])
        await client.connect()
        if not await client.is_user_authorized():
            print(f"Session {phone} is not authenticated, skipping")
            return None
        print(f"Using session {phone} to view message {msg_id} in channel {Helping_channel_id}")
        # Try to get channel entity, join if not a member
        try:
            channel_entity = await client.get_entity(int(Helping_channel_id))
        except Exception as entity_err:
            print(f"Entity error for {Helping_channel_id} on {phone}: {entity_err}")
            # Try to join channel using invite link if available
            import config
            Helping_channel_link = getattr(config, 'Helping_channel_link', None)
            try:
                if Helping_channel_link:
                    await client(ImportChatInviteRequest(Helping_channel_link.split('/')[-1]))
                    print(f"{phone} joined channel via invite link")
                    channel_entity = await client.get_entity(int(Helping_channel_id))
                else:
                    print(f"No invite link available for channel {Helping_channel_id}")
                    return None
            except Exception as join_err:
                print(f"Failed to join channel {Helping_channel_id} with {phone}: {join_err}")
                # If FROZEN_METHOD_INVALID or any error, skip this session for this channel
                print(f"Session {phone} cannot join channel {Helping_channel_id}. Skipping this session for this channel.")
                return None
        channel_peer = InputPeerChannel(
            channel_id=channel_entity.id,
            access_hash=channel_entity.access_hash
        )
        # Increment views
        msg_id_int = int(msg_id)
        try:
            result = await client(GetMessagesViewsRequest(
                peer=channel_peer,
                id=[msg_id_int],
                increment=True
            ))
        except Exception as view_err:
            print(f"Error incrementing views for {msg_id_int} with {phone}: {view_err}")
            return None
        print(f"Successfully incremented views for message {msg_id_int} using {phone}")
        # Get current view count for monitoring
        try:
            messages = await client.get_messages(int(Helping_channel_id), ids=[msg_id_int])
            if messages and messages[0]:
                current_views = messages[0].views
                print(f"Current view count for message {msg_id_int}: {current_views}")
                return True
        except Exception as e:
            print(f"Error getting message view count: {e}")
        return True
    except Exception as e:
        print(f"Error processing view with {phone}: {e}")
        return None
    finally:
        if client:
            await client.disconnect()


async def Increasing_views():
    """Main function to increase views across all channels and messages in parallel"""
    try:
        # Load database
        try:
            with open(Database, 'r', encoding='utf-8') as db_file:
                data = json.load(db_file)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error reading database: {e}")
            return
        
        # Get all session files
        sessions_dir = "sessions"
        session_files = [file.replace(".session", "") for file in os.listdir(sessions_dir) if file.endswith(".session")]
        
        if not session_files:
            print("No session files found.")
            return
        
        # Print number of available sessions
        print(f"Found {len(session_files)} session files")
        
        # Create a queue of all messages that need views
        message_queue = []
        
        # First collect all messages that need views and their required view counts
        for channel_id, channel_data in data.items():
            msg_ids = channel_data.get('msg_ids', {})
            views_per_minute = channel_data.get('views_per_minute', 0)
            
            if not msg_ids or views_per_minute <= 0:
                continue
            
            for msg_id, max_views in list(msg_ids.items()):
                if max_views <= 0:
                    continue
                
                # Calculate views to add for this message in this cycle
                views_to_add = min(views_per_minute, max_views)
                
                # Add this message to the queue multiple times based on views_to_add
                for _ in range(views_to_add):
                    message_queue.append({
                        'channel_id': channel_id,
                        'msg_id': msg_id,
                        'max_views': max_views
                    })
        
        if not message_queue:
            print("No messages to process")
            return
        
        # Shuffle the queue to randomize which messages get processed first
        random.shuffle(message_queue)
        
        total_views = len(message_queue)
        print(f"Processing {total_views} views across {len(set(item['msg_id'] for item in message_queue))} messages")
        
        # Calculate max parallel workers (based on available sessions but not too many)
        max_workers = min(len(session_files), 10, total_views)
        
        # Create a worker pool using asyncio tasks
        # Calculate time intervals - we want to spread the views evenly over a minute
        # with enough time for all tasks to complete
        time_per_view = 60.0 / total_views if total_views > 0 else 1.0
        
        # Track completed and failed views for database updates
        completed_views = []
        failed_views = []
        
        # Create a semaphore to limit concurrent tasks
        semaphore = asyncio.Semaphore(max_workers)
        
        async def worker(message_info, session_phone, max_retries=3):
            """Worker function to process a single view, with retries"""
            async with semaphore:
                channel_id = message_info['channel_id']
                msg_id = message_info['msg_id']
                attempt = 0
                while attempt < max_retries:
                    result = await process_view(session_phone, msg_id, channel_id, Helping_channel_id)
                    if result:
                        completed_views.append({
                            'channel_id': channel_id,
                            'msg_id': msg_id
                        })
                        break
                    else:
                        attempt += 1
                        print(f"Retrying view for message {msg_id} (attempt {attempt})")
                        await asyncio.sleep(1)
                if attempt == max_retries:
                    failed_views.append({
                        'channel_id': channel_id,
                        'msg_id': msg_id,
                        'phone': session_phone
                    })
        
        # Create all tasks
        tasks = []
        start_time = time.time()
        
        for i, message_info in enumerate(message_queue):
            # Select a random session for this view
            session_phone = random.choice(session_files)
            delay = i * time_per_view
            task = asyncio.create_task(
                asyncio.wait_for(
                    asyncio.gather(
                        asyncio.sleep(delay),
                        worker(message_info, session_phone, max_retries=3)
                    ),
                    timeout=50.0
                )
            )
            tasks.append(task)
        
        # Wait for all tasks to complete (or timeout)
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            print(f"Error waiting for tasks: {e}")
        
        # Update the database with completed views
        for view_info in completed_views:
            channel_id = view_info['channel_id']
            msg_id = view_info['msg_id']
            
            if channel_id in data and msg_id in data[channel_id]['msg_ids']:
                # Decrement the max_views counter
                data[channel_id]['msg_ids'][msg_id] -= 1
                
                # Remove the message if max_views reached zero
                if data[channel_id]['msg_ids'][msg_id] <= 0:
                    print(f"Message {msg_id} in channel {channel_id} reached target views, removing from queue")
                    del data[channel_id]['msg_ids'][msg_id]
        
        # Save the updated database
        try:
            temp_file = f"{Database}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as db_file:
                json.dump(data, db_file)
            os.replace(temp_file, Database)
            print(f"Database updated successfully")
        except Exception as e:
            print(f"Error updating database: {e}")
        
        elapsed_time = time.time() - start_time
        print(f"Completed {len(completed_views)} out of {total_views} views in {elapsed_time:.2f} seconds")
        if failed_views:
            print("\nFailed to increment views for the following message IDs and phone numbers:")
            for fail in failed_views:
                print(f"Channel: {fail['channel_id']}, Message ID: {fail['msg_id']}, Phone: {fail['phone']}")
        else:
            print("All views processed successfully!")
        
    except Exception as e:
        print(f"Error in Increasing_views: {e}")

def start_increasing_views_thread():
    """Start a background thread that runs the view incrementing process"""
    def run_loop():
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Get number of CPU cores for optimal performance
        cpu_count = multiprocessing.cpu_count()
        print(f"System has {cpu_count} CPU cores")
        
        while True:
            try:
                # Run the increasing views function with proper async handling
                start_time = time.time()
                print("\n=== Starting new view processing cycle ===")
                
                # Run the async function in the event loop
                loop.run_until_complete(Increasing_views())
                
                # Calculate how long this cycle took
                elapsed = time.time() - start_time
                print(f"Cycle completed in {elapsed:.2f} seconds")
                
                # Calculate wait time - we want to start a new cycle roughly once per minute
                # but allow at least 5 seconds between cycles to prevent system overload
                wait_time = max(5, 60 - elapsed)
                print(f"Waiting {wait_time:.2f} seconds before starting next cycle...")
                time.sleep(wait_time)
                
            except Exception as e:
                print(f"Error in view increasing thread: {e}")
                # Wait longer on error to prevent rapid error loops
                print("Error occurred, waiting 30 seconds before retry...")
                time.sleep(30)
    
    # Start the thread
    t = threading.Thread(target=run_loop, daemon=True)
    t.start()
    print("View increaser thread started successfully - running in parallel mode")

def command_handler():
    import asyncio
    from telegram.ext import CallbackQueryHandler

    # Join all sessions to the channel before starting the bot
    # asyncio.run(join_all_sessions_to_channel())

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("add_channel", add_channel))
    app.add_handler(CommandHandler("variation", variation))
    app.add_handler(CommandHandler("set_target", set_target))
    app.add_handler(CommandHandler("increase_views", increase_views))

    app.add_handler(CallbackQueryHandler(Button_handler))
    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, Manage_postes))
    app.add_handler(MessageHandler(filters.TEXT, Message_handler))  # Handle text messages

    # Schedule Increasing_views to run every 60 seconds using the job queue
    start_increasing_views_thread()

    print("Bot started. Press Ctrl+C to stop.")
    # Some versions of asyncio/telegram expect an event loop to exist in the main thread.
    # Ensure one is set so `asyncio.get_event_loop()` in the library does not raise.
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    except Exception:
        pass

    app.run_polling()



if __name__ == "__main__":
    command_handler()