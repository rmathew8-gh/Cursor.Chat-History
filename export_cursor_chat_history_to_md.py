#!/usr/bin/env python3
import sqlite3
import json
from pathlib import Path
from datetime import datetime
import os
import base64

def extract_conversations_from_db(db_path):
    """Extract all conversations from the database with detailed error handling."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all composer data entries
        cursor.execute("SELECT key, value FROM cursorDiskKV WHERE key LIKE 'composerData:%'")
        rows = cursor.fetchall()
        
        conversations = []
        for key, value in rows:
            try:
                # Try different methods to decode the value
                try:
                    data = json.loads(value)
                except json.JSONDecodeError:
                    try:
                        # Try decoding as base64
                        decoded = base64.b64decode(value)
                        data = json.loads(decoded)
                    except:
                        print(f"Failed to decode data for key {key}")
                        continue
                
                # Only include conversations with messages
                if data.get('conversation') and len(data['conversation']) > 0:
                    conversations.append({
                        'id': key.split(':')[1],
                        'data': data
                    })
            except Exception as e:
                print(f"Error processing conversation {key}: {e}")
        
        conn.close()
        return conversations
    except Exception as e:
        print(f"Error accessing database {db_path}: {e}")
        return []

def format_message(msg):
    """Format a single message with all its components."""
    if not isinstance(msg, dict):
        return "Invalid message format"
    
    formatted = []
    
    # Add timestamp and role
    timestamp = datetime.fromtimestamp(
        msg.get('timingInfo', {}).get('clientStartTime', 0) / 1000
    ).strftime("%Y-%m-%d %H:%M:%S")
    role = "User" if msg.get('type') == 1 else "Assistant"
    formatted.append(f"**{role}** ({timestamp}):")
    
    # Add message text
    text = msg.get('text', '').strip()
    if text:
        formatted.append(text)
    
    # Add code blocks
    if 'codeBlocks' in msg:
        for block in msg['codeBlocks']:
            lang = block.get('language', '')
            code = block.get('code', '')
            if code:
                formatted.append(f"```{lang}\n{code}\n```")
    
    # Add file actions
    if 'fileActions' in msg:
        formatted.append("\n**File Actions:**")
        for action in msg['fileActions']:
            formatted.append(f"- {action['type']}: {action.get('path', 'unknown path')}")
            if 'content' in action:
                formatted.append(f"```\n{action['content']}\n```")
    
    return "\n\n".join(formatted)

def main():
    """Main function to export all chat history."""
    mac_cursor_dir = Path(os.path.expanduser("~")) / "Library/Application Support/Cursor"
    linux_cursor_dir = Path(os.path.expanduser("~")) / ".config/Cursor/User/workspaceStorage"
    # global_db = cursor_dir / "User/globalStorage/state.vscdb"
    # global_db = '/home/roy/.config/Code/User/globalStorage/state.vscdb'
    # global_db = '/home/roy/.config/Code/User/workspaceStorage/05ddfa7c39aabef8627c3029111c6c09/state.vscdb'
    
    print(f"Extracting conversations from {global_db}")
    conversations = extract_conversations_from_db(global_db)
    
    # Sort conversations by timestamp
    conversations.sort(
        key=lambda x: x['data']['conversation'][0].get('timingInfo', {}).get('clientStartTime', 0)
        if x['data'].get('conversation') else 0
    )
    
    # Generate markdown
    output = ["# Cursor Chat History\n"]
    for conv in conversations:
        first_msg_time = datetime.fromtimestamp(
            conv['data']['conversation'][0].get('timingInfo', {}).get('clientStartTime', 0) / 1000
        ).strftime("%Y-%m-%d %H:%M:%S")
        
        output.append(f"## Conversation {conv['id']}\n")
        output.append(f"*Started at: {first_msg_time}*\n")
        
        for msg in conv['data']['conversation']:
            output.append(format_message(msg))
            output.append("\n---\n")
        
        output.append("\n")
    
    # Write to file
    output_dir = Path("chat_history_exports")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"cursor_chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(output))
    
    print(f"Exported {len(conversations)} conversations to {output_file}")

if "__main__" == __name__:
    main()
