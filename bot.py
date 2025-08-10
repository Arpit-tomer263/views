from telegram import Update,InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, filters,ApplicationBuilder,ContextTypes
from telethon.tl.functions.messages import GetMessagesViewsRequest
import random
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import InputPeerChannel
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
    with open(Database, 'r') as db_file:
        data = json.load(db_file)
        for idx,data in data.items():
            name = await get_channel_name(idx, context)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(text=name, callback_data=f"set_variation_{idx}")]
            ])
            await update.message.reply_text("Choose the channel.", reply_markup=keyboard)

# set_target
async def set_target(update:Update,context:CallbackContext):
    with open(Database, 'r') as db_file:
        data = json.load(db_file)
        for idx,data in data.items():
            name = await get_channel_name(idx, context)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(text=name, callback_data=f"set_target_{idx}")]
            ])
            await update.message.reply_text("Choose the channel.", reply_markup=keyboard)

# increase_views
async def increase_views(update: Update, context: CallbackContext):
    with open(Database, 'r') as db_file:
        data = json.load(db_file)
        for idx, data in data.items():
            name = await get_channel_name(idx, context)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(text=name, callback_data=f"increase_views_{idx}")]
            ])
            await update.message.reply_text("Choose the channel.", reply_markup=keyboard)

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

async def Manage_postes(update:Update,context: ContextTypes.DEFAULT_TYPE):
    import random
    print("new Post")
    if not update.channel_post:
        print("Returning......")
        return
    
    data = {}
    channel_id = update.channel_post.chat.id
    message_id = update.channel_post.message_id
    
    try:
        with open(Database,'r') as db_file:
            data = json.load(db_file)
        
        if str(channel_id) in data:
            channel_data = data[str(channel_id)]
            views_per_minute = channel_data.get('views_per_minute', 0)
            target_views = channel_data.get('target_views', 0)
            variation = channel_data.get('variation', 0)
            print(f"Channel ID: {channel_id}, Message ID: {message_id}, Views per minute: {views_per_minute}, Target views: {target_views}, Variation: {variation}")
            # Calculate max_view based on the formula
            if target_views > 0 and variation > 0:
                if Helping_channel_id:
                    await context.bot.forward_message(
                        chat_id=Helping_channel_id,
                        from_chat_id=channel_id,
                        message_id=message_id
                    )
                # Step 1: Calculate a = (Target_view/100 * variation)
                a = (target_views * variation) / 100
                
                # Step 2: Calculate b = Target_view - a
                b = target_views - a
                
                # Step 3: Choose random Plus or Minus 
                if random.choice([True, False]):
                    # Add a to b
                    max_view = target_views + a
                else:
                    # Subtract a from b
                    max_view = target_views - a
                
                # Make sure max_view is divisible by views_per_minute
                if views_per_minute > 0:
                    remainder = max_view % views_per_minute
                    if remainder != 0:
                        max_view = max_view - remainder  # Adjust to make it divisible
                
                # Round to integer
                max_view = int(max_view)
                
                # Store the message_id with its max_view
            
                phone_number = "+254781177515"
                app_id = 26028732
                hash_id = "d89ca58ace3c3e35f73f7e5448b2dbd6"
                client = TelegramClient(f"sessions/{phone_number}.session", app_id, hash_id)
                try:
                    await client.start()
                    if not client.is_user_authorized():
                        print(f"User is not authorized")
                        return
                        
                    # Get the message ID from the helping channel
                    last_msg = await client.get_messages(int(Helping_channel_id))
                    message_id = last_msg[0].id
                    
                    # Update the database with the new message
                    channel_data['msg_ids'][str(message_id)] = max_view
                    
                    # Write to database using a temporary file for safety
                    temp_file = f"{Database}.tmp"
                    with open(temp_file, 'w') as db_file:
                        json.dump(data, db_file)
                    os.replace(temp_file, Database)
                finally:
                    # Always disconnect the client to prevent database locks
                    await client.disconnect()
                print(f"Forwarding post from {channel_id} with settings: {views_per_minute}, {target_views}, {variation}")
                print(f"Message ID {message_id} stored with max_view: {max_view}")
            
            # Forward the message to the helping channel
            
                
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
        
        # Get channel entity and create peer
        channel_entity = await client.get_entity(int(Helping_channel_id))
        channel_peer = InputPeerChannel(
            channel_id=channel_entity.id,
            access_hash=channel_entity.access_hash
        )
        
        # Increment views
        msg_id_int = int(msg_id)
        result = await client(GetMessagesViewsRequest(
            peer=channel_peer,
            id=[msg_id_int],
            increment=True
        ))
        
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
        
        # Track completed views for database updates
        completed_views = []
        
        # Create a semaphore to limit concurrent tasks
        semaphore = asyncio.Semaphore(max_workers)
        
        async def worker(message_info, session_phone):
            """Worker function to process a single view"""
            async with semaphore:
                channel_id = message_info['channel_id']
                msg_id = message_info['msg_id']
                
                # Process the view
                result = await process_view(session_phone, msg_id, channel_id, Helping_channel_id)
                
                if result:
                    # Record successful view
                    completed_views.append({
                        'channel_id': channel_id,
                        'msg_id': msg_id
                    })
        
        # Create all tasks
        tasks = []
        start_time = time.time()
        
        for i, message_info in enumerate(message_queue):
            # Select a random session for this view
            session_phone = random.choice(session_files)
            
            # Calculate delay to stagger the tasks over the minute
            delay = i * time_per_view
            
            # Create a delayed task
            task = asyncio.create_task(
                asyncio.wait_for(
                    asyncio.gather(
                        asyncio.sleep(delay),
                        worker(message_info, session_phone)
                    ),
                    timeout=50.0  # Ensure tasks don't run too long
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
    app.run_polling()



if __name__ == "__main__":
    command_handler()