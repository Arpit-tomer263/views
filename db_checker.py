"""
Database Checker Utility
This script provides a simple way to check the status of the database.json file
and see what channels and messages are being processed.
"""

import json
import os
from config import Database

def display_database_status():
    """Display the current status of the database"""
    try:
        if not os.path.exists(Database):
            print(f"Error: Database file '{Database}' does not exist.")
            return
            
        with open(Database, 'r', encoding='utf-8') as db_file:
            data = json.load(db_file)
            
        print("\n===== DATABASE STATUS =====")
        print(f"Total channels: {len(data)}")
        
        total_views_per_minute = 0
        total_messages = 0
        
        for channel_id, channel_data in data.items():
            views_per_minute = channel_data.get('views_per_minute', 0)
            target_views = channel_data.get('target_views', 0)
            variation = channel_data.get('variation', 0)
            msg_ids = channel_data.get('msg_ids', {})
            
            total_views_per_minute += views_per_minute
            total_messages += len(msg_ids)
            
            print(f"\nChannel ID: {channel_id}")
            print(f"  Views per minute: {views_per_minute}")
            print(f"  Target views: {target_views}")
            print(f"  Variation: {variation}%")
            print(f"  Messages: {len(msg_ids)}")
            
            for msg_id, max_views in msg_ids.items():
                print(f"    Message {msg_id}: {max_views} views remaining")
                
        print("\n===== SUMMARY =====")
        print(f"Total channels: {len(data)}")
        print(f"Total messages: {total_messages}")
        print(f"Total views per minute: {total_views_per_minute}")
        
        if total_views_per_minute > 0:
            interval = 60.0 / total_views_per_minute
            print(f"Approximate interval between views: {interval:.2f} seconds")
            
    except json.JSONDecodeError:
        print(f"Error: Database file '{Database}' is not valid JSON.")
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    display_database_status()
