# archbyte

A Python library for Telegram automation and group management.

**Author:** Cyrus Arch

## Installation

```bash
pip install archbyte
```

## Features

- Session-based authentication with persistent login
- Bulk leave operations with rate limiting
- Whitelist protection for important chats
- Keyword-based spam detection and auto-leave
- Activity logging and tracking
- Async/await support with context managers

## Quick Start

```python
import asyncio
from archbyte import Telecemper

async def main():
    client = Telecemper(
        api_id='YOUR_API_ID',
        api_hash='YOUR_API_HASH',
        phone_number='+1234567890'
    )
    
    # First time authentication
    await client.request_code()
    code = input("Enter code: ")
    message, session = await client.authenticate(code)
    
    # Save session for future use
    print(f"Session: {session}")
    
    await client.disconnect()

asyncio.run(main())
```

## Configuration

Get your API credentials from https://my.telegram.org

Required:
- `api_id` - Telegram API ID
- `api_hash` - Telegram API hash  
- `phone_number` - Phone number with country code

## Usage Examples

### Using saved session

```python
client = Telecemper(
    api_id='YOUR_API_ID',
    api_hash='YOUR_API_HASH',
    phone_number='+1234567890',
    session_string='YOUR_SAVED_SESSION'
)

await client.login_with_session()
```

### Whitelist management

```python
# Add chats to whitelist (by ID, username, or title)
client.add_to_whitelist(123456789, "family_group", "Work Team")

# Load from file
client.load_whitelist_from_file("whitelist.txt")

# Save to file
client.save_whitelist_to_file("whitelist.txt")

# View protected chats
protected = client.get_whitelist()
```

### Bulk operations

```python
# Leave all chats except whitelisted
summary = await client.leave_all_chats(
    delay_range=(1, 5),
    respect_whitelist=True
)

print(f"Left: {summary['left_count']}")
print(f"Protected: {summary['skipped_count']}")
```

### Spam detection

```python
# Enable auto-leave on spam keywords
keywords = ['free giveaway', 'get rich quick', 'limited offer']
await client.enable_spam_detection(keywords)

# Disable spam detection
client.disable_spam_detection()
```

### List all chats

```python
chats = await client.list_all_chats()
for chat in chats:
    status = "Protected" if chat['protected'] else "Unprotected"
    print(f"{chat['title']}: {status}")
```

### View logs

```python
logs = client.get_logs()
print(logs['leave_log'])
print(logs['join_log'])
print(logs['activity_log'])
```

## Whitelist File Format

Create a `whitelist.txt` file with one identifier per line:

```
# Comments start with #
123456789
family_chat
Work Team
987654321
```

## API Reference

### Authentication Methods

- `request_code()` - Request verification code
- `authenticate(code)` - Authenticate with code, returns session string
- `login_with_session()` - Login with saved session

### Whitelist Methods

- `add_to_whitelist(*identifiers)` - Add chats to whitelist
- `remove_from_whitelist(*identifiers)` - Remove from whitelist
- `clear_whitelist()` - Clear all whitelist items
- `get_whitelist()` - Get list of whitelisted items
- `load_whitelist_from_file(filepath)` - Load from file
- `save_whitelist_to_file(filepath)` - Save to file

### Operation Methods

- `leave_all_chats(delay_range, respect_whitelist)` - Leave all groups/channels
- `list_all_chats(include_protected)` - List all chats with status
- `enable_spam_detection(keywords)` - Enable auto-leave on spam
- `disable_spam_detection()` - Disable spam detection
- `get_logs()` - Retrieve activity logs

### Utility Methods

- `start()` - Start the client
- `disconnect()` - Disconnect the client

## Context Manager

```python
async with Telecemper(api_id, api_hash, phone, session) as client:
    await client.leave_all_chats()
    # Automatically disconnects on exit
```

## Logging

Configure Python logging to see detailed activity:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Best Practices

- Store session strings securely, never commit to version control
- Use delays between operations to respect rate limits
- Always whitelist important chats before bulk operations
- Monitor logs for unexpected behavior
- Use context managers for automatic cleanup

## License

MIT License, 
