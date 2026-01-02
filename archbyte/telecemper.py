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
    """Telegram client wrapper for managing group/channel memberships."""
    
    def __init__(self, api_id, api_hash, phone_number, session_string=None):
        """
        Initialize Telecemper client.
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API hash
            phone_number: Phone number for authentication
            session_string: Optional session string for re-authentication
        """
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
    
    async def _ensure_client(self):
        """Initialize client if not already connected."""
        if self.client is None:
            self.client = TelegramClient(
                StringSession(self.session_string), 
                self.api_id, 
                self.api_hash
            )
            await self.client.connect()
    
    async def request_code(self):
        """Request authentication code from Telegram."""
        await self._ensure_client()
        await self.client.send_code_request(self.phone_number)
        return "Verification code sent to your Telegram app."
    
    async def authenticate(self, code):
        """
        Authenticate with verification code.
        
        Args:
            code: Verification code from Telegram
            
        Returns:
            tuple: (success_message, session_string)
        """
        try:
            await self.client.sign_in(phone=self.phone_number, code=code)
            self.session_string = self.client.session.save()
            await self._setup_activity_handler()
            return "Authentication successful.", self.session_string
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return f"Authentication failed: {str(e)}", None
    
    async def login_with_session(self):
        """Login using saved session string."""
        try:
            await self._ensure_client()
            if await self.client.is_user_authorized():
                await self._setup_activity_handler()
                return "Logged in successfully with session."
            return "Session authentication failed. Please re-authenticate."
        except Exception as e:
            logger.error(f"Session login failed: {e}")
            return f"Session login failed: {str(e)}"
    
    async def enable_spam_detection(self, keywords):
        """
        Enable automatic spam detection and leaving.
        
        Args:
            keywords: List of keywords/phrases to detect as spam.
                     Messages containing any of these will trigger auto-leave.
        
        Example:
            await client.enable_spam_detection([
                'free giveaway', 'get rich quick', 'limited offer'
            ])
        """
        if not isinstance(keywords, list):
            raise ValueError("keywords must be a list of strings")
        
        self._spam_keywords = [k.lower() for k in keywords]
        
        if not self._spam_detector_active:
            @self.client.on(events.NewMessage())
            async def spam_detector(event):
                if event.is_private or not self._spam_keywords:
                    return
                
                message = event.message.text.lower() if event.message.text else ""
                
                if any(keyword in message for keyword in self._spam_keywords):
                    await self._leave_chat(
                        await event.get_chat(), 
                        reason=f"spam detected: matched keyword"
                    )
            
            self._spam_detector_active = True
            logger.info(f"Spam detection enabled with {len(keywords)} keywords")
        else:
            logger.info(f"Spam detection updated with {len(keywords)} keywords")
        
        return f"Spam detection enabled with {len(self._spam_keywords)} keywords."
    
    def disable_spam_detection(self):
        """Disable automatic spam detection."""
        self._spam_keywords = []
        logger.info("Spam detection disabled")
        return "Spam detection disabled."
    
    async def _setup_activity_handler(self):
        """Set up event handlers for activity logging."""
        
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
        """
        Leave a chat/channel.
        
        Args:
            chat: Chat or Channel entity
            reason: Reason for leaving
            delay: Optional delay before leaving
        """
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
    
    async def leave_all_chats(self, delay_range=(1, 5)):
        """
        Leave all groups and channels.
        
        Args:
            delay_range: Tuple of (min, max) seconds to delay between operations
            
        Returns:
            str: Summary of operation
        """
        dialogs = await self.client.get_dialogs()
        chats = [d for d in dialogs if isinstance(d.entity, (Chat, Channel))]
        total = len(chats)
        left = 0
        
        for dialog in chats:
            delay = random.uniform(*delay_range)
            await self._leave_chat(
                dialog.entity, 
                reason="bulk cleanup",
                delay=delay
            )
            left += 1
            
            progress = f"Progress: {left}/{total}"
            logger.info(f"{progress} (delay: {delay:.2f}s)")
        
        return f"Left {left} out of {total} chats."
    
    def get_logs(self):
        """Get all logs."""
        return {
            'leave_log': self.leave_log,
            'join_log': self.join_log,
            'activity_log': self.activity_log
        }
    
    async def start(self):
        """Start the client (convenience method)."""
        await self._ensure_client()
        if not await self.client.is_user_authorized():
            raise RuntimeError("Client not authorized. Please authenticate first.")
        await self.client.start(phone=self.phone_number)
    
    async def disconnect(self):
        """Disconnect the client."""
        if self.client:
            await self.client.disconnect()
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()