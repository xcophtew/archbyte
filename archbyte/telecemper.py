from telethon import TelegramClient, events
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.sessions import StringSession
from telethon.tl.types import Channel, Chat
import asyncio
import logging
from datetime import datetime
import random

logger = logging.getLogger(__name__)


class Telecemper:
    
    def __init__(self, api_id, api_hash, phone_number, session_string=None):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.session_string = session_string
        
        self.client = None
        self.leave_log = []
        self.join_log = []
        self.activity_log = []
        self._spam_detector_active = False
        self._spam_keywords = []
        self._whitelist = set()
    
    async def _ensure_client(self):
        if self.client is None:
            self.client = TelegramClient(
                StringSession(self.session_string), 
                self.api_id, 
                self.api_hash
            )
            await self.client.connect()
    
    async def request_code(self):
        await self._ensure_client()
        await self.client.send_code_request(self.phone_number)
        return "Verification code sent to your Telegram app."
    
    async def authenticate(self, code):
        try:
            await self.client.sign_in(phone=self.phone_number, code=code)
            self.session_string = self.client.session.save()
            await self._setup_activity_handler()
            return "Authentication successful.", self.session_string
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return f"Authentication failed: {str(e)}", None
    
    async def login_with_session(self):
        try:
            await self._ensure_client()
            if await self.client.is_user_authorized():
                await self._setup_activity_handler()
                return "Logged in successfully with session."
            return "Session authentication failed. Please re-authenticate."
        except Exception as e:
            logger.error(f"Session login failed: {e}")
            return f"Session login failed: {str(e)}"
    
    def add_to_whitelist(self, *identifiers):
        for identifier in identifiers:
            if isinstance(identifier, int):
                self._whitelist.add(identifier)
            elif isinstance(identifier, str):
                self._whitelist.add(identifier)
                self._whitelist.add(identifier.lower().strip())
        
        logger.info(f"Added {len(identifiers)} items to whitelist")
        return f"Whitelist updated. Total protected: {len(self._whitelist)} items"
    
    def remove_from_whitelist(self, *identifiers):
        removed = 0
        for identifier in identifiers:
            if isinstance(identifier, int):
                if identifier in self._whitelist:
                    self._whitelist.remove(identifier)
                    removed += 1
            elif isinstance(identifier, str):
                for version in [identifier, identifier.lower().strip()]:
                    if version in self._whitelist:
                        self._whitelist.discard(version)
                        removed += 1
        
        logger.info(f"Removed {removed} items from whitelist")
        return f"Removed {removed} items. Remaining: {len(self._whitelist)} items"
    
    def clear_whitelist(self):
        count = len(self._whitelist)
        self._whitelist.clear()
        logger.info("Whitelist cleared")
        return f"Whitelist cleared. Removed {count} items"
    
    def get_whitelist(self):
        return list(self._whitelist)
    
    def load_whitelist_from_file(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            self.add_to_whitelist(int(line))
                        except ValueError:
                            self.add_to_whitelist(line)
            
            logger.info(f"Loaded whitelist from {filepath}")
            return f"Loaded whitelist from file. Total items: {len(self._whitelist)}"
        except FileNotFoundError:
            logger.error(f"Whitelist file not found: {filepath}")
            return f"Error: File not found - {filepath}"
        except Exception as e:
            logger.error(f"Error loading whitelist: {e}")
            return f"Error loading whitelist: {str(e)}"
    
    def save_whitelist_to_file(self, filepath):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("# Telecemper Whitelist\n")
                f.write("# One identifier per line (chat ID, username, or title)\n\n")
                for item in sorted(self._whitelist, key=str):
                    f.write(f"{item}\n")
            
            logger.info(f"Saved whitelist to {filepath}")
            return f"Whitelist saved to {filepath}"
        except Exception as e:
            logger.error(f"Error saving whitelist: {e}")
            return f"Error saving whitelist: {str(e)}"
    
    def _is_whitelisted(self, chat):
        if chat.id in self._whitelist:
            return True
        
        if hasattr(chat, 'username') and chat.username:
            if chat.username in self._whitelist or chat.username.lower() in self._whitelist:
                return True
        
        if hasattr(chat, 'title') and chat.title:
            if chat.title in self._whitelist or chat.title.lower().strip() in self._whitelist:
                return True
        
        return False
    
    async def list_all_chats(self, include_protected=True):
        await self._ensure_client()
        dialogs = await self.client.get_dialogs()
        chats_info = []
        
        for dialog in dialogs:
            if isinstance(dialog.entity, (Chat, Channel)):
                is_protected = self._is_whitelisted(dialog.entity)
                
                if not include_protected and is_protected:
                    continue
                
                info = {
                    'id': dialog.entity.id,
                    'title': dialog.entity.title,
                    'username': getattr(dialog.entity, 'username', None),
                    'protected': is_protected,
                    'type': 'Channel' if isinstance(dialog.entity, Channel) else 'Group'
                }
                chats_info.append(info)
        
        return chats_info
    
    async def enable_spam_detection(self, keywords):
        if not isinstance(keywords, list):
            raise ValueError("keywords must be a list of strings")
        
        self._spam_keywords = [k.lower() for k in keywords]
        
        if not self._spam_detector_active:
            @self.client.on(events.NewMessage())
            async def spam_detector(event):
                if event.is_private or not self._spam_keywords:
                    return
                
                chat = await event.get_chat()
                
                if self._is_whitelisted(chat):
                    return
                
                message = event.message.text.lower() if event.message.text else ""
                
                if any(keyword in message for keyword in self._spam_keywords):
                    await self._leave_chat(chat, reason=f"spam detected: matched keyword")
            
            self._spam_detector_active = True
            logger.info(f"Spam detection enabled with {len(keywords)} keywords")
        else:
            logger.info(f"Spam detection updated with {len(keywords)} keywords")
        
        return f"Spam detection enabled with {len(self._spam_keywords)} keywords."
    
    def disable_spam_detection(self):
        self._spam_keywords = []
        logger.info("Spam detection disabled")
        return "Spam detection disabled."
    
    async def _setup_activity_handler(self):
        
        @self.client.on(events.ChatAction)
        async def activity_tracker(event):
            chat = await event.get_chat()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if event.user_added:
                user = await event.get_user()
                me = await self.client.get_me()
                
                if event.user_id == me.id:
                    msg = f"Added to {chat.title}"
                    self.join_log.append(msg)
                    self.activity_log.append(f"[{timestamp}] {msg}")
                    logger.info(msg)
                else:
                    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                    msg = f"{name} added to {chat.title}"
                    self.activity_log.append(f"[{timestamp}] {msg}")
                    logger.info(msg)
            
            elif event.user_kicked or event.user_left:
                user = await event.get_user()
                name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                msg = f"{name} left {chat.title}"
                self.activity_log.append(f"[{timestamp}] {msg}")
                logger.info(msg)
    
    async def _leave_chat(self, chat, reason="manual", delay=None):
        try:
            if delay:
                await asyncio.sleep(delay)
            
            if isinstance(chat, Channel):
                await self.client(LeaveChannelRequest(chat))
            elif isinstance(chat, Chat):
                await self.client.delete_dialog(chat)
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_msg = f"Left {chat.title} ({reason})"
            
            self.leave_log.append(log_msg)
            self.activity_log.append(f"[{timestamp}] {log_msg}")
            logger.info(log_msg)
            
        except Exception as e:
            error_msg = f"Failed to leave {chat.title}: {e}"
            self.leave_log.append(error_msg)
            self.activity_log.append(f"[{datetime.now()}] {error_msg}")
            logger.error(error_msg)
    
    async def leave_all_chats(self, delay_range=(1, 5), respect_whitelist=True):
        dialogs = await self.client.get_dialogs()
        chats = [d for d in dialogs if isinstance(d.entity, (Chat, Channel))]
        
        left_chats = []
        skipped_chats = []
        
        for dialog in chats:
            chat = dialog.entity
            
            if respect_whitelist and self._is_whitelisted(chat):
                skipped_chats.append(chat.title)
                logger.info(f"Skipped (whitelisted): {chat.title}")
                continue
            
            delay = random.uniform(*delay_range)
            await self._leave_chat(chat, reason="bulk cleanup", delay=delay)
            left_chats.append(chat.title)
            
            progress = f"Progress: {len(left_chats)}/{len(chats) - len(skipped_chats)}"
            logger.info(f"{progress} (delay: {delay:.2f}s)")
        
        summary = {
            'left_count': len(left_chats),
            'skipped_count': len(skipped_chats),
            'total_processed': len(chats),
            'left_chats': left_chats,
            'skipped_chats': skipped_chats
        }
        
        return summary
    
    def get_logs(self):
        return {
            'leave_log': self.leave_log,
            'join_log': self.join_log,
            'activity_log': self.activity_log
        }
    
    async def start(self):
        await self._ensure_client()
        if not await self.client.is_user_authorized():
            raise RuntimeError("Client not authorized. Please authenticate first.")
        await self.client.start(phone=self.phone_number)
    
    async def disconnect(self):
        if self.client:
            await self.client.disconnect()
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()