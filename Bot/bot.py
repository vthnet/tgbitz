#---------- © sᴛᴀʟᴋᴇʀ@hehe_stalker
#---------- ᴘʀᴏJᴇᴄᴛ - ᴛᴇʟᴇɢʀᴀᴍ ᴀᴜᴛᴏᴍᴀᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛ sᴇʟʟɪɴɢ ʙᴏᴛ
#-------------------------------------------------------
import os
from html import escape
import sqlite3
from server3 import register_server3_handlers
from buysrc_panels import register_buysrc_panels_handlers
from aiogram.types import LinkPreviewOptions
import re
from server2_api import get_available_countries 
import provider 
from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable
from aiogram.types import TelegramObject
import shutil
import glob
from aiogram.types import BufferedInputFile
import io
from server2_handlers import register_server2_handlers
import time
import zipfile
from aiogram.types import FSInputFile
import asyncio
from utils import fmt_curr, update_usdt_rate_task
import html
from bson import Binary
from telethon.tl.functions.account import UpdatePasswordSettingsRequest, GetPasswordRequest
from aiogram.types import CopyTextButton
from telethon.tl.functions.account import GetAuthorizationsRequest, ResetAuthorizationRequest
from aiogram.fsm.context import FSMContext
from datetime import datetime, timezone, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pymongo import MongoClient
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PasswordHashInvalidError
import re
# Add this near your other imports at the top
from smmpanel import register_smmpanel_handlers



# Create the SMM prices collection
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.messages import SendReactionRequest, SendVoteRequest, ImportChatInviteRequest
from telethon.tl.types import ReactionEmoji
from urllib.parse import urlparse
from telethon.tl.functions.messages import GetMessagesViewsRequest
####------------server 4 ------------
from server4 import register_server4_handlers
# # ... plus your existing import
from telethon.errors import PasswordHashInvalidError
from aiogram.utils.deep_linking import create_start_link
from bson import ObjectId
from aiogram import types
import random
import math
from aiogram.types import InputMediaVideo
from recharge_flow import register_recharge_handlers
from mustjoin import check_join
from config import BOT_TOKEN, ADMIN_IDS

# ================= MongoDB Setup =================
MONGO_URI = os.getenv("MONGO_URI") or "mongodb+srv://brimreading_db_user:Valrikthakur0@cluster0.jxl0eok.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["tgbitz"]
users_col = db["users"]
orders_col = db["orders"]
countries_col = db["countries"]
numbers_col = db["numbers"]
crypto_col = db["crypto_invoices"]
withdrawals_col = db["withdrawals"]
admins_col = db["admins"]
smm_col = db["smm_prices"]
settings_col = db["settings"]
#--------- Config : don't use @
BOTUSER = "tgbitz_bot"
SUPPORT = "ogbitz"
USAGE = "tgbitz"
OWNER = "tgbitz_op"
UPDATES= "tgbitz"
CHANNEL="tgbitz"

SALESLOG = "-1004484806488"
ADMINLOG = "-1004492615113"
SALES = "-1004484806488"
CHANNEL = "tgbitz"
TEMPORASMS_API_KEY = "yyy"
exchange_rate = "95.0"
# Simple Anti-Spam Dictionary
# Default SMM prices fallback if admin hasn't set them
# Default SMM Initializer (Run once to populate default values)
default_services = ["votes", "joins", "reactions", "mass_dm", "vote_poll", "views"]
for s in default_services:
    if not smm_col.find_one({"service": s}):
        smm_col.insert_one({"service": s, "price": 2.0, "min_buy": 5})

# ================= Ban Middleware =================
class BanCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")
        if user:
            user_doc = users_col.find_one({"_id": user.id})
            if user_doc and user_doc.get("banned", False):
                # If event is a message, reply. If callback, answer alert.
                if isinstance(event, Message):
                    await event.answer("🚫 <b>You are banned from using this bot.</b>", parse_mode="HTML")
                elif isinstance(event, CallbackQuery):
                    await event.answer("🚫 You are banned from using this bot.", show_alert=True)
                return # Stop processing
        return await handler(event, data)

# Store user interaction timestamps
action_cooldowns = {}

def is_on_cooldown(user_id: int, cd_seconds: int = 3) -> bool:
    now = time.time()
    last_action = action_cooldowns.get(user_id, 0)
    if now - last_action < cd_seconds:
        return True
    action_cooldowns[user_id] = now
    return False
    
        
# ================= Bot Setup =================
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
dp.update.middleware(BanCheckMiddleware()) # <--- ADD THIS LINE
dp["db"] = db 




# ================= FSM =================
class AddSession(StatesGroup):
    waiting_country = State()
    waiting_number = State()
    waiting_otp = State()
    waiting_password = State()
    waiting_next_action = State()   # ✅ REQUIRD
class SeparateFSM(StatesGroup):
    waiting_for_zip = State()
    choosing_extension = State()
class BulkChange2FAFSM(StatesGroup):
    waiting_for_zip = State()
    waiting_for_current_pass = State()
    waiting_for_new_pass = State()
    

class ManualAddFSM(StatesGroup):
    waiting_country = State()
    waiting_number = State()
    waiting_otp = State()
    waiting_pass = State()
    viewing_results = State()
    waiting_new_2fa = State()
    

# --- FSM States for Session Buying ---
class BuySessionFlow(StatesGroup):
    waiting_for_quantity = State()
    waiting_for_2fa_password = State() # <-- Add this line

class ZipperFSM(StatesGroup):
    waiting_for_count = State()
    waiting_for_files = State()
    waiting_for_zip_name = State()
class SellSession(StatesGroup):
    # ... existing states ...
    waiting_sell_number = State()

class WithdrawState(StatesGroup):
    waiting_upi = State()
    waiting_amount = State()

class ConvertSessionFSM(StatesGroup):
    waiting_for_zip = State()
    

class AdminTxnState(StatesGroup):
    waiting_txn = State()
    # Define a state for searching
class SpamCheckSorterFSM(StatesGroup):
    waiting_for_zip = State()

class ShopStates(StatesGroup):
    searching_country = State()

class ReadSessionFSM(StatesGroup):
    waiting_for_zip = State()

class CreateSessionFSM(StatesGroup):
    waiting_number = State()
    waiting_otp = State()
    waiting_pass = State()
    waiting_next_action = State()
    
# --- Define FSM States ---
class WithdrawState(StatesGroup):
    waiting_inr_upi = State()
    waiting_inr_amount = State()
    
    waiting_usdt_method = State()
    waiting_usdt_address = State()
    waiting_usdt_amount = State()

class AdminTxnState(StatesGroup):
    waiting_txn = State()



# --- FSM States ---
class BulkAddSession(StatesGroup):
    waiting_for_zip = State()
    waiting_for_global_pass = State()
    processing = State()
    viewing_results = State()
    waiting_country_selection = State()
    waiting_new_2fa = State()  

class AddCountryFSM(StatesGroup):
    waiting_data = State()



class EditCountryFSM(StatesGroup):
    waiting_new_name = State()
    waiting_new_price = State()


class SMMAdminFlow(StatesGroup):
    waiting_for_price = State()

class SMMBuyFlow(StatesGroup):
    waiting_qty = State()
    waiting_channel_link = State()
    waiting_post_link = State()
    waiting_reaction_type = State()
    waiting_dm_type = State()
    waiting_vote_button = State()     # NEW: For inline buttons
    waiting_poll_option = State()     
    waiting_dm_target = State()
    waiting_dm_custom_text = State()

# ================= FSM for /check =================
class CheckSessionsAdmin(StatesGroup):
    waiting_new_2fa = State()
    waiting_freeze_country = State()

def recount_stock(country_name):
    """Helper to recalculate and sync unified stock counter."""
    total = numbers_col.count_documents({"country": country_name, "used": False})
    countries_col.update_one(
        {"name": country_name}, 
        {"$set": {"stock": total}}
    )

async def get_usdt_inr_rate() -> float:
    url = "https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=inr"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("tether", {}).get("inr", 85.0) # Fallback to 85.0 if parsing fails
    except Exception as e:
        print(f"Error fetching USDT rate: {e}")
    return 93.0 # Fallback rate if API is down
def get_or_create_user(user_id: int, username: str | None):
    user = users_col.find_one({"_id": user_id})
    if not user:
        user = {"_id": user_id, "username": username or None, "balance": 0.0}
        users_col.insert_one(user)
    return user

def is_admin(user_id: int) -> bool:
    # Always allow hardcoded owners
    if user_id in ADMIN_IDS:
        return True
    # Check if user is in the extra admins database
    extra_admin = admins_col.find_one({"_id": user_id})
    return extra_admin is not None


def get_user_balance(user_id):
    user = users_col.find_one({"_id": user_id})
    return user.get("balance", 0) if user else 0

def save_session_to_db(phone: str, session_path: str, country: str, status: str = "active", password: str = None):
    """Saves a physical SQLite session file into MongoDB as Binary data."""
    with open(f"{session_path}.session", "rb") as f:
        session_data = Binary(f.read())
    
    numbers_col.update_one(
        {"number": phone},
        {
            "$set": {
                "country": country,
                "session_file": session_data,
                "password": password,
                "status": status,
                "used": False
            }
        },
        upsert=True
    )
    # Increment unified stock counter
    countries_col.update_one({"name": country}, {"$inc": {"stock": 1}})
def fix_telethon_session(db_path: str):
    """Forces the session file to match Telethon's exact expected 5-column schema."""
    try:
        # Telethon uses the path without the extension, so ensure we target the physical file
        actual_path = f"{db_path}.session" if not db_path.endswith(".session") else db_path
        
        with sqlite3.connect(actual_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
            if not cursor.fetchone():
                return # Not a valid sqlite db

            # Check existing columns
            cursor.execute("PRAGMA table_info(sessions)")
            columns_info = cursor.fetchall()
            column_names = [info[1] for info in columns_info]
            
            # If it perfectly matches the 5 columns Telethon expects, do nothing
            expected_cols = ['dc_id', 'server_address', 'port', 'auth_key', 'takeout_id']
            if len(column_names) == 5 and all(c in column_names for c in expected_cols):
                return

            # Read the active session data
            cursor.execute("SELECT * FROM sessions")
            row = cursor.fetchone()

            if not row:
                return

            # Map the data (safely handling Pyrogram or missing columns)
            data_map = dict(zip(column_names, row))
            
            dc_id = data_map.get('dc_id', 2)
            server_address = data_map.get('server_address', '149.154.167.50') # Safe fallback
            port = data_map.get('port', 443)
            auth_key = data_map.get('auth_key', b'')
            takeout_id = data_map.get('takeout_id', None)

            # Wipe and rebuild the table to Telethon's EXACT specification
            cursor.execute("DROP TABLE sessions")
            cursor.execute('''
                CREATE TABLE sessions (
                    dc_id integer primary key,
                    server_address text,
                    port integer,
                    auth_key blob,
                    takeout_id integer
                )
            ''')
            cursor.execute(
                "INSERT INTO sessions VALUES (?, ?, ?, ?, ?)",
                (dc_id, server_address, port, auth_key, takeout_id)
            )
            conn.commit()
    except Exception as e:
        print(f"Session fix error for {db_path}: {e}")

        
def load_session_from_db(phone: str, target_path: str) -> bool:
    """Extracts the Binary session data from MongoDB to a local SQLite file."""
    doc = numbers_col.find_one({"number": phone})
    if not doc or "session_file" not in doc:
        return False
    
    with open(f"{target_path}.session", "wb") as f:
        f.write(doc["session_file"])
    return True

# --- Helper for Progress Bar ---
def get_prog_bar(current, total):
    percent = (current / total) * 100
    bar = "🟢" * int(percent // 10) + "⚪" * (10 - int(percent // 10))
    return f"{bar} {percent:.1f}%"

    
async def otp_listener(number_doc, user_id, message_id):
    phone = number_doc["number"]
    session_path = f"temp_sessions/run_{phone}_{int(time.time())}"
    os.makedirs("temp_sessions", exist_ok=True)
    
    # 1. Extract physical SQLite file from DB
    if not load_session_from_db(phone, session_path):
        return
        
    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")
    client = TelegramClient(session_path, api_id, api_hash)
    
    try:
        await client.connect()
        if not await client.is_user_authorized():
            return

        pattern = re.compile(r"\b\d{5}\b") 
        async for msg in client.iter_messages(777000, limit=10):
            if not msg.message: continue
            match = pattern.search(msg.message)
            if not match: continue

            # OTP FOUND!
            code = match.group(0)
            password_text = number_doc.get("password") or "None"

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="Copy OTP", copy_text=CopyTextButton(text=code)),
                    InlineKeyboardButton(text="Copy Pass", copy_text=CopyTextButton(text=password_text))
                ],
                [InlineKeyboardButton(text="• Get Code Again •", callback_data=f"get_otp:{phone}")]
            ])

            await bot.edit_message_text(
                chat_id=user_id, message_id=message_id,
                text=(
                    f"<pre>Order Completed ✅</pre>\n"
                    f"✅ 𝐍𝗨𝐌𝐁𝐄𝐑 - <code>+{phone}</code>\n"
                    f"💬 𝐂𝐎𝐃𝐄 - <code>{code}</code>\n"
                    f"💬 𝐏𝐀𝐒𝐒 - <code>{password_text}</code>"
                ), parse_mode="HTML", reply_markup=kb
            )

            
            # ===== USER & LOGGING =====
            user = users_col.find_one({"_id": user_id}) or {}
            buyer_name = user.get("username") or f"User {user_id}"
            balance = user.get("balance", "N/A")

            country = number_doc.get("country", "Unknown")
            price = number_doc.get("price", "N/A")
            number = str(number_doc.get("number", "Unknown"))

            if number != "Unknown":
                if not number.startswith("+"):
                    number = f"+{number}"
                masked_number = number[:6] + "•••••"
            else:
                masked_number = "Hidden"

            channel_message = (
                f"<pre><u>✅ <b>New Number Purchase Successful</b></u></pre>\n\n"
                f"➖ <b><u>Country:</u></b> {country}\n"
                f"➖ <b><u>Application:</u> Теlegгам 🍷</b>\n\n"
                f"➕ <b>Number: {masked_number} 📞</b>\n"
                f"➕ <b>OTP:</b> <span class='tg-spoiler'>{code}</span> 💬\n"
                f"➕ <b>Server:</b> (1) 🥂\n"
                f"➕ <b>Password:</b> <span class='tg-spoiler'>{password_text}</span> 🔐\n\n"
                f"<b>• @tgbitz_bot || @tgbitz</b>"
            )

                                    # --- DYNAMIC DEEP LINK FOR SERVER 1 LOGS (Fixed: Safe Hex ID Mapping) ---
            country_doc = countries_col.find_one({"name": country})
            if country_doc:
                clean_id_param = str(country_doc["_id"])
            else:
                clean_id_param = country.replace(" ", "_")

            buy_button = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"• Buy {country} Now •",
                            url=f"https://t.me/{BOTUSER}?start=buy_s1_{clean_id_param}"
                        )
                    ]
                ]
            )


        
            

            await bot.send_message(
                "-1003349993686",
                channel_message,
                parse_mode="HTML",
                reply_markup=buy_button
            )

            admin_message = (
                f"<pre>📢 New Purchase Alert</pre>\n\n"
                f"<b>• Application:</b> Telegram\n"
                f"<b>• Country:</b> {country}\n"
                f"<b>• Number:</b> {number}\n"
                f"<b>• OTP:</b> <code>{code}</code>\n"
                f"➖ <b>Password:</b> <span class='tg-spoiler'>{password_text}</span> 🔐\n\n"
                f"<b>👤 User:</b> @{buyer_name} (<code>{user_id}</code>)\n"
                f"<b>💰 Balance:</b> {balance}"
            )
            userbutton = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="USER ID",
                            url=f"tg://openmessage?user_id={user_id}"
                        )
                    ]
                ]
            )

            await bot.send_message(
                "-1003208353049",
                admin_message,
                parse_mode="HTML",
                reply_markup=userbutton
            )

            # Update DB OTP log
            numbers_col.update_one(
                {"_id": number_doc["_id"]},
                {"$set": {"last_otp": code, "otp_fetched_at": datetime.now(timezone.utc)}}
            )
            break
            
        await asyncio.sleep(1)
        
    except Exception as e:
        print(f"OTP Listener Error: {e}")
    finally:
        if client.is_connected():
            await client.disconnect()
        # Clean up physical file after OTP check to save local disk space
        if os.path.exists(f"{session_path}.session"):
            os.remove(f"{session_path}.session")
            

# /addadmin - Only for Owners
@dp.message(Command("addadmin"))
async def cmd_add_admin(msg: Message):
    # Only Owners (-7659846392, 7217739116) can add new admins
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("❌ Only Owners can promote new admins.")

    args = msg.text.split()
    if len(args) != 2:
        return await msg.answer("⚠️ Usage: /addadmin <code>user_id</code>")

    try:
        new_admin_id = int(args[1])
        admins_col.update_one({"_id": new_admin_id}, {"$set": {"added_by": msg.from_user.id}}, upsert=True)
        await msg.answer(f"✅ User <code>{new_admin_id}</code> is now an Admin.")
    except ValueError:
        await msg.answer("❌ Invalid User ID.")

# /removeadmin - Only for Owners
@dp.message(Command("removeadmin"))
async def cmd_remove_admin(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("❌ Only Owners can remove admins.")

    args = msg.text.split()
    if len(args) != 2:
        return await msg.answer("⚠️ Usage: /removeadmin <code>user_id</code>")

    try:
        target_id = int(args[1])
        if target_id in ADMIN_IDS:
            return await msg.answer("❌ You cannot remove a hardcoded Owner.")
        
        result = admins_col.delete_one({"_id": target_id})
        if result.deleted_count > 0:
            await msg.answer(f"🗑️ User <code>{target_id}</code> removed from admins.")
        else:
            await msg.answer("❌ User not found in database admin list.")
    except ValueError:
        await msg.answer("❌ Invalid User ID.")

# /admins - For all admins to see the list
@dp.message(Command("admins"))
async def cmd_list_admins(msg: Message):
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ Not authorized.")

    # Get DB admins
    db_admins = list(admins_col.find({}))
    
    text = "👑 <b>Bot Admins</b>\n\n"
    text += "<b>Owners (Hardcoded):</b>\n"
    for owner in ADMIN_IDS:
        text += f"• <code>{owner}</code>\n"
    
    if db_admins:
        text += "\n<b>Added Admins:</b>\n"
        for adm in db_admins:
            text += f"• <code>{adm['_id']}</code>\n"
    
    await msg.answer(text, parse_mode="HTML")
    

@dp.callback_query(F.data.startswith("manage_devices:"))
async def manage_devices(call: CallbackQuery):
    number = call.data.split(":", 1)[1]
    doc = numbers_col.find_one({"number": number})

    if not doc or not doc.get("string_session"):
        return await call.answer("❌ No active session", show_alert=True)

    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")

    client = TelegramClient(
        StringSession(doc["string_session"]),
        api_id,
        api_hash
    )
    await client.connect()

    try:
        sessions = await client(GetAuthorizationsRequest())
    except Exception:
        await client.disconnect()
        return await call.answer("❌ Failed to fetch sessions", show_alert=True)

    kb = InlineKeyboardMarkup(inline_keyboard=[])

    for s in sessions.authorizations:
        if s.current:
            continue  # cannot remove current via hash

        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{s.device_model} | {s.platform}",
                callback_data=f"kill_session:{number}:{s.hash}"
            )
        ])

    await client.disconnect()

    if not kb.inline_keyboard:
        return await call.message.answer("✅ No removable sessions")

    await call.message.answer(
        "📱 Click any session to remove:",
        reply_markup=kb
    )


#-----Temrinate sessuon
@dp.callback_query(F.data.startswith("kill_session:"))
async def kill_session(call: CallbackQuery):
    _, number, session_hash = call.data.split(":")
    doc = numbers_col.find_one({"number": number})

    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")

    client = TelegramClient(
        StringSession(doc["string_session"]),
        api_id,
        api_hash
    )
    await client.connect()

    try:
        await client(ResetAuthorizationRequest(hash=int(session_hash)))
        await call.answer("✅ Session removed", show_alert=True)
    except Exception:
        await call.answer("❌ Cannot remove session", show_alert=True)
    finally:
        await client.disconnect()

    #&------Logout bot

@dp.callback_query(F.data.startswith("logout_bot:"))
async def logout_bot(call: CallbackQuery):
    number = call.data.split(":", 1)[1]
    doc = numbers_col.find_one({"number": number})

    if not doc or not doc.get("string_session"):
        return await call.answer("❌ No active session", show_alert=True)

    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")

    client = TelegramClient(StringSession(doc["string_session"]), api_id, api_hash)
    await client.connect()

    try:
        await client.log_out()
    finally:
        await client.disconnect()

    # 🔥 VERY IMPORTANT
    numbers_col.update_one(
        {"number": number},
        {
            "$set": {
                "active": False,   # session dead
                "used": True
            },
            "$unset": {
                "string_session": ""
            }
        }
    )

    await call.message.answer(
        "✅ Bot session has been logged out\nOTP polling closed for this number"
    )

# ================= Reusable Deep Link UI Generators =================
async def send_s1_country_menu_direct(target_msg: Message, country_name: str):
    country = countries_col.find_one({"name": country_name})
    if not country:
        return await target_msg.answer(f"❌ Country <b>{country_name}</b> is currently out of stock or unavailable.", parse_mode="HTML")

    text = (
        f"<blockquote>"
        f"🌍 <b>Country:</b> {country_name}\n"
        f"🏷️ <b>Price:</b> {fmt_curr(country.get('price', 0))}\n"
        f"📦 <b>Stock:</b> {country.get('stock', 0)}"
        f"</blockquote>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Buy Now", callback_data=f"buy_now:{country_name}")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="buy_server1", icon_custom_emoji_id="5409284148491726576", style="danger")]
    ])
    await target_msg.answer(text, parse_mode="HTML", reply_markup=kb)

# ================ START =================
@dp.message(Command("start"), F.chat.type == "private")
async def cmd_start(m: Message, state: FSMContext):
    await state.clear()
    
    user_id = m.from_user.id
    
    # Check if the user is completely new before adding them to the database
    is_new_user = users_col.find_one({"_id": user_id}) is None
    
    # 1. Ensure User Exists in DB
    user = get_or_create_user(m.from_user.id, m.from_user.username)
    
    # Send notification to admins if it's a first-time user
    if is_new_user:
        user_count = users_col.count_documents({})
        username_text = f"@{m.from_user.username}" if m.from_user.username else "None"
        
        admin_alert = (
            f"<b><u>New user started bot</u></b>\n\n"
            f"<b>Name</b>- {m.from_user.full_name}\n"
            f"<b>Username</b>- {username_text}\n"
            f"<b>User Id</b>- {user_id}\n\n"
            f"<b>User count</b> - {user_count}"
        )
        
        # Loop through your hardcoded admin list from config
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(chat_id=admin_id, text=admin_alert)
            except Exception as e:
                print(f"Could not send new user log to admin {admin_id}: {e}")


    
    # 2. Check Mandatory Channel Join
    if not await check_join(bot, m):
        return

    # 3. Parse Deep Link Arguments
    args = m.text.split()
    if len(args) > 1:
        param = args[1]
        
        # --- REFERRAL LINK ---
        if param.startswith("ref"):
            try:
                referrer_id = int(param.replace("ref", ""))
                if referrer_id != user_id and users_col.find_one({"_id": referrer_id}):
                    if not users_col.find_one({"_id": user_id}).get("referred_by"):
                        users_col.update_one({"_id": user_id}, {"$set": {"referred_by": referrer_id}})
                        await m.answer(f"👋 <b>Welcome!</b>\nYou were referred by user ID: <code>{referrer_id}</code>", parse_mode="HTML")
            except ValueError:
                pass
                
                # --- SERVER 1 DEEP LINK (Fixed: Using Hex ID instead of Raw Name) ---
        elif param.startswith("buy_s1_"):
            country_hex_id = param.replace("buy_s1_", "")
            try:
                # Direct safe conversion to MongoDB ObjectId lookup
                country_doc = countries_col.find_one({"_id": ObjectId(country_hex_id)})
                if country_doc:
                    return await send_s1_country_menu_direct(m, country_doc["name"])
                else:
                    # Fallback string parser logic for backwards compatibility with old log messages
                    country_name = country_hex_id.replace("_", " ")
                    return await send_s1_country_menu_direct(m, country_name)
            except Exception:
                country_name = country_hex_id.replace("_", " ")
                return await send_s1_country_menu_direct(m, country_name)

            
        # --- SERVER 2 DEEP LINK (e.g. buy_s2_US) ---
        elif param.startswith("buy_s2_"):
            country_code = param.replace("buy_s2_", "").upper()
            try:
                from server2_handlers import send_s2_country_menu_direct
                return await send_s2_country_menu_direct(m, country_code, user_id, m.from_user.username)
            except Exception as e:
                print(f"Server 2 Deep Link Error: {e}")
                
        # --- SERVER 3 DEEP LINK (e.g. buy_s3_tg_USA) ---
        elif param.startswith("buy_s3_"):
            parts = param.replace("buy_s3_", "").split("_", 1)
            if len(parts) == 2:
                service, country_name = parts[0], parts[1].replace("_", " ")
                try:
                    from server3 import send_s3_operator_menu_direct
                    return await send_s3_operator_menu_direct(m, service, country_name, fmt_curr)
                except Exception as e:
                    print(f"Server 3 Deep Link Error: {e}")

    # 4. Show Standard Main Menu if no valid deep link was triggered
    full_name = m.from_user.full_name
    username = f"@{m.from_user.username}" if m.from_user.username else "@no-username"
    safe_name = escape(full_name)
    user_mention = f"<a href='tg://user?id={user_id}'>{safe_name}</a>"
    balance_val = user.get('balance', 0.0)
    balance = fmt_curr(balance_val)
    
    caption = (
        f'<tg-emoji emoji-id="6111431921802155977">🤖</tg-emoji> <b>TG BITZ BOT</b>\n\n'
        f'<blockquote expandable><tg-emoji emoji-id="5409132617750555920">🤩</tg-emoji> <b>Name<a href="https://files.catbox.moe/ebra5w.jpg">:</a></b> {user_mention}\n'
        f'<tg-emoji emoji-id="5408846628763217930">👤</tg-emoji> <b>User ID:</b> {user_id}\n'
        f'<tg-emoji emoji-id="5408924092793368814">👤</tg-emoji> <b>Username:</b> {username}\n'
        f'<tg-emoji emoji-id="5911101139444567404">💸</tg-emoji> <b>Balance:</b> {balance}</blockquote>\n––––––—–————––––——–––•\n'
        f'<tg-emoji emoji-id="5409194306365829029">✈️</tg-emoji> <b>Support</b> : @ogbitz'
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Sell Account", callback_data="sell", icon_custom_emoji_id="5262828387923158890"),
            InlineKeyboardButton(text="Buy Account", callback_data="buy", icon_custom_emoji_id="5262747715552438702")
        ],
        [
            InlineKeyboardButton(text="Buy & Sell Sessions", callback_data="sbsessions", icon_custom_emoji_id="6084477132254218612")
        ],
        [
            InlineKeyboardButton(text="SMM-Panel", callback_data="feature_smm_external", icon_custom_emoji_id="5389057356493511934")
        ],
        [InlineKeyboardButton(text="Manage Session files",url="https://t.me/Bitz_Session_Manager_bot?start=starting",icon_custom_emoji_id="5298853345241358103")
        ],
        [
            InlineKeyboardButton(text="Source Codes", callback_data="buy_src_menu", icon_custom_emoji_id="6084477132254218612"),
            InlineKeyboardButton(text="Buy Panels", callback_data="buy_panel_menu", icon_custom_emoji_id="6084477132254218612")
        ],
        [
            InlineKeyboardButton(text="Recharge", callback_data="recharge", icon_custom_emoji_id="5201873447554145566"),
            InlineKeyboardButton(text="Profile", callback_data="stats", icon_custom_emoji_id="6014823049159773944")
        ],
        [
            InlineKeyboardButton(text="More", callback_data="more_menu", icon_custom_emoji_id="4974546038372172354"),
            InlineKeyboardButton(text="Feedback", url="https://t.me/bitzfeedbackbot?start=starting", icon_custom_emoji_id="5262838597060422237")
        ]
    ])
    
    await m.answer(
        text=caption, 
        parse_mode="HTML", 
        reply_markup=kb,
        link_preview_options=LinkPreviewOptions(show_above_text=True)
    )


    


# ================= More.. Menu =================
@dp.callback_query(lambda cq: cq.data == "more_menu")
async def more_menu(cq: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Sales Log", url=f"https://t.me/tgbitz_log")],
        [InlineKeyboardButton(text="Refer", callback_data="refer")],
        [InlineKeyboardButton(text="Redeem", callback_data="redeem"),],
        [InlineKeyboardButton(text="About Account", callback_data="stats")],
        [InlineKeyboardButton(text="Refer & Earn", callback_data="refer")],
        [InlineKeyboardButton(text="Contact Support", url=f"https://t.me/ogbitz")],
        [InlineKeyboardButton(text="How to Buy Account", url=f"https://t.me/tgbitz_guidence/4")],
        [InlineKeyboardButton(text="How to Sell Account", url=f"https://t.me/tgbitz_guidence/5")],
        [InlineKeyboardButton(text="How to Recharge", url=f"https://t.me/tgbitz_guidence/6")],
        [InlineKeyboardButton(text="Buy Source Code", callback_data="buy_src_menu", icon_custom_emoji_id="6084477132254218612"),
        InlineKeyboardButton(text="Buy Panels", callback_data="buy_panel_menu", icon_custom_emoji_id="6084477132254218612")],
        [InlineKeyboardButton(text="Back", callback_data="back_main", icon_custom_emoji_id="5409284148491726576", style="danger")]
    ])

    await cq.message.edit_text(
        "<b>View more services and help :</b>",
        parse_mode="HTML",
        reply_markup=kb
    )
    await cq.answer()  # optional: remove "loading..." notification


#=============== Back Button =================
@dp.callback_query(lambda cq: cq.data == "back_main")
async def back_main(cq: CallbackQuery):
    if not await check_join(bot, cq):
        await cq.answer("❗ Join the channel first", show_alert=True)
        return
    user_id = cq.from_user.id
    full_name = cq.from_user.full_name  # always use the name
    safe_name = escape(full_name)
    # --- New Username Logic ---
    if cq.from_user.username:
        username = f"@{cq.from_user.username}"
    else:
        username = "@no-username"
    # --------------------------
    user_mention = f"<a href='tg://user?id={user_id}'>{safe_name}</a>"
    user = users_col.find_one({"_id": user_id})
    balance_val = user.get('balance', 0.0) if user else 0.0
    balance = fmt_curr(balance_val)
    
    # Rebuild main menu dynamically (reuse your send_main_menu logic)
    
    caption = (
        f'<tg-emoji emoji-id="6111431921802155977">🤖</tg-emoji> <b>TG BITZ BOT</b>\n\n'
        f'<blockquote expandable><tg-emoji emoji-id="5409132617750555920">🤩</tg-emoji> <b>Name<a href="https://files.catbox.moe/ebra5w.jpg">:</a></b> {user_mention}\n'
        f'<tg-emoji emoji-id="5408846628763217930">👤</tg-emoji> <b>User ID:</b> {user_id}\n'
        f'<tg-emoji emoji-id="5408924092793368814">👤</tg-emoji> <b>Username:</b> {username}\n'
        f'<tg-emoji emoji-id="5911101139444567404">💸</tg-emoji> <b>Balance:</b> {balance}</blockquote>\n––––––—–————––––——–––•\n'
        f'<tg-emoji emoji-id="5409194306365829029">✈️</tg-emoji> <b>Support</b> : @ogbitz'
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Sell Account", callback_data="sell", icon_custom_emoji_id="5262828387923158890"),
            InlineKeyboardButton(text="Buy Account", callback_data="buy", icon_custom_emoji_id="5262747715552438702")
        ],
        [
            InlineKeyboardButton(text="Buy & Sell Sessions", callback_data="sbsessions", icon_custom_emoji_id="6084477132254218612")
        ],
        [
            InlineKeyboardButton(text="SMM-Panel", callback_data="feature_smm_external", icon_custom_emoji_id="5389057356493511934")
        ],
        [InlineKeyboardButton(text="Manage Session files",url="https://t.me/Bitz_Session_Manager_bot?start=starting",icon_custom_emoji_id="5298853345241358103")
                ],
        [
            InlineKeyboardButton(text="Source Codes", callback_data="buy_src_menu", icon_custom_emoji_id="6084477132254218612"),
            InlineKeyboardButton(text="Buy Panels", callback_data="buy_panel_menu", icon_custom_emoji_id="6084477132254218612")
        ],
        
        [
            InlineKeyboardButton(text="Recharge", callback_data="recharge", icon_custom_emoji_id="5201873447554145566"),
            InlineKeyboardButton(text="Profile", callback_data="stats", icon_custom_emoji_id="6014823049159773944")
        ],
        [
            InlineKeyboardButton(text="More", callback_data="more_menu", icon_custom_emoji_id="4974546038372172354"),
            InlineKeyboardButton(text="Feedback", url="https://t.me/bitzfeedbackbot?start=starting", icon_custom_emoji_id="5262838597060422237")
    
        ]
       
    ])
    
    try:
        await cq.message.edit_text(
            text=caption,
            parse_mode="HTML",
            reply_markup=kb,
            link_preview_options=LinkPreviewOptions(show_above_text=True)
    )
    except Exception:
    # Current message may be a photo/media message.
    # Media messages cannot be converted to text with edit_text(),
    # so delete it and send a fresh home menu.
        try:
            await cq.message.delete()
        except Exception:
            pass

        await cq.message.answer(
            text=caption,
            parse_mode="HTML",
        reply_markup=kb,
        link_preview_options=LinkPreviewOptions(show_above_text=True)
    )

    await cq.answer()

# --- Feature Alerts ---

@dp.callback_query(F.data == "feature_api")
async def callback_api_soon(cq: CallbackQuery):
    """Callback for the API button"""
    await cq.answer(
        "🚀 API Integration\n\nThis feature is coming soon! You will be able to connect your services via API shortly.",
        show_alert=True
    )


    
#================ Balance =================
@dp.callback_query(F.data == "balance")
async def show_balance(cq: CallbackQuery):
    user = users_col.find_one({"_id": cq.from_user.id})
    await cq.answer(f"💰 Balance: {fmt_curr(user['balance']) if user else fmt_curr(0)}", show_alert=True)

@dp.message(Command("balance"))
async def cmd_balance(msg: Message):
    user = users_col.find_one({"_id": msg.from_user.id})
    await msg.answer(f"💰 Balance: {fmt_curr(user['balance']) if user else fmt_curr(0)}")



@dp.callback_query(F.data == "sbsessions")
async def callback_sbsessions(cq: CallbackQuery):
    await cq.answer()
    user_id = cq.from_user.id
    user = users_col.find_one({"_id": user_id})
    balance_val = user.get('balance', 0.0) if user else 0.0
    balance = fmt_curr(balance_val)

    text = (
        f"📄 <b>buy and sell sessions system:</b>\n––––––—–————––––——–––•\n"
        f"<u>• Advanced and robust protection\n"
        f"• Works automatically and quickly</u>\n"
        f"• <b>Total balance</b>: {balance}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛒 Buy sessions", callback_data="buy_sessions")
        ],
        [InlineKeyboardButton(text="💸 Sell Mass Accounts",url="https://t.me/bitz_receiver_bot")
        ],
        [
            InlineKeyboardButton(text="▪️ Back", callback_data="back_main", icon_custom_emoji_id="5409284148491726576", style="danger")
        ]
    ])

    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    
#= =============== Buy Flow =================

# Initial "Buy" message with server selection
@dp.callback_query(lambda c: c.data == "buy")
async def callback_buy(cq: CallbackQuery):
    await cq.answer()
    user = get_or_create_user(cq.from_user.id, cq.from_user.username)  # Fetch user info

    text = (
        f'<tg-emoji emoji-id="5262747715552438702">🥂</tg-emoji> <b>Buy Ready Telegram Accounts</b>:\n'
        f'––––––—————––––——–––•\n'
        f'<blockquote><tg-emoji emoji-id="5409337058193847247">🥂</tg-emoji> 100% activation & code delivery</blockquote>\n'
        f'<blockquote><tg-emoji emoji-id="5409337058193847247">🥂</tg-emoji> High-quality accounts [No Spam]</blockquote>\n'
        f'<blockquote><tg-emoji emoji-id="5408943604829794451">🥂</tg-emoji> Tap on get otp button only after login the given number in app</blockquote>\n'
        f'<b><tg-emoji emoji-id="5409078930659357770">🥂</tg-emoji> Total balance -</b> {fmt_curr(user["balance"])}\n➖➖➖➖➖➖➖➖➖➖➖'
    )

    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="Server- 1 (Basic TG)", callback_data="buy_server1", icon_custom_emoji_id="6296218646284863141")
    )
    kb.row(
        InlineKeyboardButton(text="Server- 2 (Good Quality TG)", callback_data="buy_server2", icon_custom_emoji_id="6296218646284863141")
    )
    kb.row(
        InlineKeyboardButton(text="Server- 3 (NUM change)", callback_data="s3_user_root", icon_custom_emoji_id="6328083463920424231")
    )
    kb.row(
        InlineKeyboardButton(text="Server- 4 (cheap phishing)", callback_data="s3tg_open", icon_custom_emoji_id="6296218646284863141")
    )
    

    kb.row(InlineKeyboardButton(text="Previous", callback_data="back_main", icon_custom_emoji_id="5409284148491726576", style="danger"))
    
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())



#Server 1 continues to normal country menu
@dp.callback_query(lambda c: c.data == "buy_server1")
async def callback_buy_server1(cq: CallbackQuery):
    await cq.answer()
    await send_country_menu(cq)  # Use the same country menu function



@dp.callback_query(F.data == "toggle_alpha")
async def toggle_alpha(cq: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    curr = data.get("sort_alpha", "A-Z")
    new_val = "Z-A" if curr == "A-Z" else "A-Z"
    await state.update_data(sort_alpha=new_val)
    await cq.answer(f"Filter changed to {new_val}", show_alert=True)
    await send_country_menu(cq, state=state)

@dp.callback_query(F.data == "toggle_price")
async def toggle_price(cq: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    curr = data.get("sort_price", "None")
    new_val = "Highest" if curr in ["None", "Cheapest"] else "Cheapest"
    await state.update_data(sort_price=new_val)
    await cq.answer(f"Sort changed to {new_val}", show_alert=True)
    await send_country_menu(cq, state=state)
    




COUNTRIES_PER_PAGE = 10

async def send_country_menu(cq: CallbackQuery, page: int = 0, search_query: str = None, state: FSMContext = None):
    await cq.answer()
    
    # 1. Fetch sort preferences from state
    sort_alpha = "A-Z"
    sort_price = "None"
    if state:
        data = await state.get_data()
        sort_alpha = data.get("sort_alpha", "A-Z")
        sort_price = data.get("sort_price", "None")
    
    countries = await asyncio.to_thread(lambda: list(countries_col.find({})))
    
    if search_query:
        countries = [c for c in countries if search_query.lower() in c["name"].lower()]

    # 2. Apply Sorting Logic
    if sort_alpha == "A-Z":
        countries.sort(key=lambda x: x.get('name', '').lower())
    elif sort_alpha == "Z-A":
        countries.sort(key=lambda x: x.get('name', '').lower(), reverse=True)
        
    if sort_price == "Cheapest":
        countries.sort(key=lambda x: x.get('price', 0))
    elif sort_price == "Highest":
        countries.sort(key=lambda x: x.get('price', 0), reverse=True)

    total = len(countries)
    if total == 0:
        msg = "❌ No countries found." if search_query else "❌ No countries available."
        kb = InlineKeyboardBuilder()
        kb.button(text="back_main", callback_data="back_main")
        return await cq.message.edit_text(msg, reply_markup=kb.as_markup())

    total_pages = math.ceil(total / COUNTRIES_PER_PAGE)
    page = max(0, min(page, total_pages - 1))
    start = page * COUNTRIES_PER_PAGE
    end = start + COUNTRIES_PER_PAGE
    paginated = countries[start:end]

    kb = InlineKeyboardBuilder()
    
    # --- Add Sort & Filter Buttons First ---
        # --- Add Sort & Filter Buttons First ---
    kb.button(text=f"Filter: {sort_alpha}", callback_data="toggle_alpha", style="danger", icon_custom_emoji_id="5408910121264756249")
    kb.button(text=f"Sort: {sort_price}", callback_data="toggle_price", style="danger", icon_custom_emoji_id="5783105032350076195")

    # --- Add Country Buttons (with prices) ---
    for c in paginated:
        price_str = fmt_curr(c.get("price", 0))
        kb.button(text=f"{c['name']} | {price_str}", callback_data=f"country:{c['name']}")
    
    kb.adjust(2) # Formats everything strictly into rows of 2

    nav_row = []
    start_page = max(0, page - 2)
    end_page = min(total_pages, start_page + 5)
    
    for p in range(start_page, end_page):
        label = f"[{p+1}]" if p == page else str(p+1)
        nav_row.append(InlineKeyboardButton(text=label, callback_data=f"countries_page:{p}"))
    
    kb.row(*nav_row)
    kb.row(
        InlineKeyboardButton(text=" ", callback_data="search_country", icon_custom_emoji_id="5429571366384842791", style="success"),
        InlineKeyboardButton(text="Home", callback_data="back_main", icon_custom_emoji_id="5409284148491726576", style="danger")
    )

    user_id = cq.from_user.id
    user = users_col.find_one({"_id": user_id})
    Balance = fmt_curr(user['balance']) if user else fmt_curr(0)

    text = (
        f"<b><u>Buy SpamFree Telegram accounts:</u></b>\n"
        f"––––––––––––––————––•\n"
        f"◍ <b><u>Total balance</u>:</b> {Balance}\n"
        f"◍ <b><u>Server</u>:</b> Server (1)\n"
        f"◍ <b><u>Page</u>:</b> {page+1} of {total_pages}\n"
        f"✅ <a href='https://t.me/tgbitz_log'>Successful Purchases</a>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖"
    )

    await cq.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML", disable_web_page_preview=True)

# ================= Callbacks & Handlers =================

@dp.callback_query(lambda c: c.data.startswith("countries_page:"))
async def paginate_countries(cq: CallbackQuery):
    page = int(cq.data.split(":")[1])
    await send_country_menu(cq, page)

@dp.callback_query(lambda c: c.data == "search_country")
async def start_search(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    sent_msg = await cq.message.answer("Type the <b>Country Name</b> you are looking for:")
    await state.set_state(ShopStates.searching_country)
    await state.update_data(last_msg_id=sent_msg.message_id, menu_msg_id=cq.message.message_id)

@dp.message(ShopStates.searching_country)
async def process_search(message: Message, state: FSMContext):
    search_query = message.text
    data = await state.get_data()
    
    # Clean up user message and prompt message
    await message.delete()
    try:
        await bot.delete_message(message.chat.id, data['last_msg_id'])
    except: pass

    # Use a dummy CallbackQuery object to reuse the send_country_menu function
    class DummyCQ:
        def __init__(self, msg):
            self.message = msg
            self.from_user = message.from_user
        async def answer(self): pass

    # Fetch the original menu message
    menu_msg = await message.answer("🔄 Searching...") # Temporary 
    dummy = DummyCQ(menu_msg)
    
    await send_country_menu(dummy, page=0, search_query=search_query)
    await state.clear()
    


# =============== Country Selection =================
@dp.callback_query(F.data.startswith("country:"))
async def callback_country(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    
    try:
        country_name = cq.data.split(":")[1]
    except IndexError:
        return await cq.message.answer("❌ Invalid button data.")
        
    country = countries_col.find_one({"name": country_name})
    if not country:
        return await cq.message.answer("❌ Country not found in database.")
        
    text = (
        f"<b>📦 Purchase Overview</b>\n"
        f"––––––––––––––————––•\n"
        f"<blockquote>"
        f"🌍 <b>Target Country:</b> <code>{country_name}</code>\n"
        f"🏷️ <b>Price per Account:</b> <code>{fmt_curr(country.get('price', 0))}</code>\n"
        f"📊 <b>Current Stock:</b> <code>{country.get('stock', 0)}</code> available\n"
        f"</blockquote>\n"
        f"<i>⚠️ Note: Ensure you read the terms before proceeding. Accounts are delivered instantly upon successful payment.</i>"
    )
    
    kb = InlineKeyboardBuilder()
    
    # Updated: Routes to buy_terms, adds requested emoji and success style
    kb.button(text="Buy Now", callback_data=f"buy_terms:{country_name}", style="success", icon_custom_emoji_id="5440841102871517055")
    # Updated: Routes to buy_server1, adds requested emoji and danger style
    kb.button(text="Back", callback_data="buy_server1", style="danger", icon_custom_emoji_id="5409284148491726576") 
    kb.adjust(1)
    
    await cq.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("buy_terms:"))
async def callback_buy_terms(cq: CallbackQuery):
    user_id = cq.from_user.id
    
    # 3-Second Cooldown Check
    if is_on_cooldown(user_id):
        return await cq.answer("⚠️ Please wait 3 seconds before clicking again...", show_alert=True)

    country_name = cq.data.split(":")[1]

    text = (
        f"<b>📝 Terms and Conditions</b>\n"
        f"––––––––––––––————––•\n"
        f"<blockquote>"
        f"By proceeding with this purchase for <b>{country_name}</b>, you agree to the tgbitz Network terms of service. "
        f"Accounts are verified and delivered instantly. Please ensure you use the OTP safely."
        f"</blockquote>\n<blockquote><u>Note:</u> Only use Telegraph or Nicegram downloaded from Playstore/Apple Store only</blockquote>"
    )

    kb = InlineKeyboardBuilder()
    # Accept routes to the final buy_now handler
    kb.button(text="Accept", callback_data=f"buy_now:{country_name}", style="success", icon_custom_emoji_id="5409135942055243844")
    # Decline routes back to the server 1 menu
    kb.button(text="Decline", callback_data="buy_server1", style="danger", icon_custom_emoji_id="5408900479063175258")
    kb.adjust(2)

    await cq.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    

@dp.callback_query(F.data.startswith("buy_now:"))
async def callback_buy_now(cq: CallbackQuery, state: FSMContext):
    if is_on_cooldown(cq.from_user.id):
        return await cq.answer("⚠️ Please wait 3 seconds before clicking other button", show_alert=True)
    await state.clear()
    
    country_name = cq.data.split(":")[1]
    user_id = cq.from_user.id
    
    country = countries_col.find_one({"name": country_name})
    user = users_col.find_one({"_id": user_id})

    if not country:
        return await cq.answer("❌ Country data not found.", show_alert=True)

    price = country.get("price", 999999)
    stock = country.get("stock", 0)
    user_balance = user.get("balance", 0.0)

    if stock < 1:
        return await cq.answer(f"⚠️ Out of Stock for {country_name}.", show_alert=True)

    if user_balance < price:
        return await cq.answer("❌ Insufficient balance. Please recharge.", show_alert=True)

    # Fetch an unused number for this country
    number_doc = numbers_col.find_one({
        "country": country_name, 
        "used": False
    })
    
    if not number_doc:
        countries_col.update_one({"name": country_name}, {"$set": {"stock": 0}})
        return await cq.answer("⚠️ Stock mismatch. Contact Admin.", show_alert=True)

    # Execute Purchase
    try:
        users_col.update_one({"_id": user_id}, {"$inc": {"balance": -price}})
        numbers_col.update_one(
            {"_id": number_doc["_id"]}, 
            {"$set": {"used": True, "owner_id": user_id, "buy_time": datetime.now(timezone.utc)}}
        )
        orders_col.insert_one({
            "user_id": user_id,
            "country": country_name,
            "number": number_doc["number"],
            "price": price,
            "status": "purchased",
            "created_at": datetime.now(timezone.utc)
        })
        countries_col.update_one({"name": country_name}, {"$inc": {"stock": -1}})
        
    except Exception as e:
        return await cq.answer("❌ Transaction failed.", show_alert=True)

    new_bal = user_balance - price
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="• Get OTP", callback_data=f"get_otp:{number_doc['number']}"),
            InlineKeyboardButton(text="Copy Num", copy_text=CopyTextButton(text=str(number_doc["number"])))
        ],
        [InlineKeyboardButton(text="• Support •", url=f"https://t.me/ogbitz")]
    ])

    success_msg = (
        f"<pre>✅ Purchased Successfully!</pre>\n"
        f"<blockquote>"
        f"🌍 <b>Country:</b> {country_name}\n"
        f"📞 <b>Number:</b> <code>+{number_doc['number']}</code>\n"
        f"🏷️ <b>Price:</b> {fmt_curr(price)}\n"
        f"💸 <b>Remaining Balance:</b> {fmt_curr(new_bal)}"
        f"</blockquote>"
    )

    await cq.message.edit_text(success_msg, parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data == "rcsessions")
async def callback_rcsessions(cq: CallbackQuery):
    await cq.answer()
    text = (
        "<b><u>Select what you want</u></b>\n––––––—–————––––——–––•\n"
        "• <u>privacy maintained</u>\n"
        "• <u>no sessions will be stored on bot server</u>\n"
        "• <b><u>Costs</u></b> : $<span class='tg-spoiler'>FREE</span>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗒️ Read session", callback_data="read_session", style="danger")],
        [InlineKeyboardButton(text="👨‍💻 Create session", callback_data="create_session", style="danger")],
        [
            InlineKeyboardButton(text="⚙️ Manage session", callback_data="sc_start", style="success"),
            InlineKeyboardButton(text="🗜️ Zip sessions", callback_data="zipper_start", style="success")
        ],
        [InlineKeyboardButton(text="Back", callback_data="back_main", icon_custom_emoji_id="5409284148491726576", style="danger")]
    ])
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

# --- Convert Session Initialization ---
@dp.callback_query(F.data == "convert_session")
async def callback_convert_session(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Home", callback_data="back_main")]
    ])
    await cq.message.edit_text(
        "🔄 <b>Session Version Converter</b>\n\n"
        "Please send a <code>.zip</code> file containing older version Telethon <code>.session</code> files.\n\n"
        "<i>The bot will automatically upgrade their SQLite database structures to the bot's current version and return them to you in a brand new zip archive.</i>", 
        parse_mode="HTML", 
        reply_markup=kb
    )
    await state.set_state(ConvertSessionFSM.waiting_for_zip)


# --- Process Zip and Convert Session Schema ---
@dp.message(StateFilter(ConvertSessionFSM.waiting_for_zip), F.document)
async def process_conversion_zip(msg: Message, state: FSMContext):
    if not msg.document.file_name.endswith('.zip'):
        return await msg.answer("❌ Please upload a valid <b>.zip</b> file context archive.")

    status_msg = await msg.answer("🔄 <i>Processing zip archive & updating database schemas... Please wait.</i>", parse_mode="HTML")
    
    # Create isolated unique paths for processing
    timestamp = int(time.time())
    extract_dir = f"temp_sessions/convert_{msg.from_user.id}_{timestamp}"
    output_dir = f"temp_sessions/output_{msg.from_user.id}_{timestamp}"
    os.makedirs(extract_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    zip_path = f"{extract_dir}/incoming.zip"
    await bot.download(msg.document, destination=zip_path)
    
    try:
        shutil.unpack_archive(zip_path, extract_dir)
        os.remove(zip_path) # Drop raw archive payload to conserve environment space
    except Exception:
        shutil.rmtree(extract_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)
        return await status_msg.edit_text("❌ Failed to parse or safely extract the uploaded ZIP file structure.")

    # Find all nested session targets recursively
    session_files = glob.glob(f"{extract_dir}/**/*.session", recursive=True)
    
    if not session_files:
        shutil.rmtree(extract_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)
        return await status_msg.edit_text("❌ Analysis complete: No valid <code>.session</code> files detected inside the archive context.")

    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")
    
    converted_count = 0
    failed_count = 0
    
    # Initialize compilation buffers
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for index, file_path in enumerate(session_files):
            # Clean absolute filenames
            base_name = os.path.basename(file_path)
            session_name = file_path[:-8] if file_path.endswith(".session") else file_path
            
            # Update live monitoring string to client UI layout
            if index % 5 == 0 or index == len(session_files) - 1:
                await status_msg.edit_text(
                    f"⚙️ <b>Migrating Databases...</b>\n"
                    f"{get_prog_bar(index + 1, len(session_files))}\n"
                    f"📊 Total Handled: {index + 1}/{len(session_files)}", 
                    parse_mode="HTML"
                )
            
            try:
                # Instantiate Telethon. This forces internal SQLiteSession initialization & handles system database structural migrations
                client = TelegramClient(session_name, api_id, api_hash)
                await client.connect()
                await client.disconnect()
                
                # Read the newly structure-migrated local file asset block
                with open(f"{session_name}.session", "rb") as f:
                    zf.writestr(base_name, f.read())
                converted_count += 1
            except Exception as error:
                print(f"Migration dropped on target file element: {base_name}. Reason: {error}")
                failed_count += 1

    # Final transmission handling
    if converted_count > 0:
        zip_buffer.seek(0)
        final_zip_file = BufferedInputFile(
            zip_buffer.read(), 
            filename=f"Converted_Sessions_{msg.from_user.id}.zip"
        )
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▪️ Main Menu", callback_data="back_main")]
        ])
        
        await msg.answer_document(
            document=final_zip_file,
            caption=(
                f"✅ <b>Database Migration Tasks Successful!</b>\n"
                f"––––––––––––––————––•\n"
                f"📦 <b>Successfully Upgraded:</b> {converted_count} Sessions\n"
                f"⚠️ <b>Corrupted/Skipped:</b> {failed_count} Files\n\n"
                f"<i>All files are fully compatible with your bot layout requirements.</i>"
            ),
            parse_mode="HTML",
            reply_markup=kb
        )
    else:
        await msg.answer("❌ Database migration failed completely. No valid profiles could be updated safely.")
        
    # Full garbage collections routines & directory scrub
    await status_msg.delete()
    shutil.rmtree(extract_dir, ignore_errors=True)
    shutil.rmtree(output_dir, ignore_errors=True)
    await state.clear()
                            
# --- Read Session Init ---
@dp.callback_query(F.data == "read_session")
async def callback_read_session(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Home", callback_data="back_main")]
    ])
    await cq.message.edit_text(
        "📂 <b>Send session zip</b>\n\n"
        "<i>Upload a .zip file containing Telethon .session (SQLite) files.</i>", 
        parse_mode="HTML", 
        reply_markup=kb
    )
    await state.set_state(ReadSessionFSM.waiting_for_zip)


# --- Create Session Init ---
@dp.callback_query(F.data == "create_session")
async def callback_create_session(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Back", callback_data="rcsessions")]
    ])
    await cq.message.edit_text(
        "📱 <b>Send number</b>\n\n"
        "<i>Enter the phone number with country code (e.g., +14151234567)</i>", 
        parse_mode="HTML", 
        reply_markup=kb
    )
    await state.set_state(CreateSessionFSM.waiting_number)

async def trigger_next_session_read(chat_id: int, state: FSMContext):
    """Helper function to process the next .session file in the queue."""
    data = await state.get_data()
    files = data.get("session_files", [])
    index = data.get("current_index", 0)

    if index >= len(files):
        await bot.send_message(chat_id, "✅ <b>All sessions processed.</b>", parse_mode="HTML")
        # Cleanup extracted files
        shutil.rmtree(data.get("extract_dir"), ignore_errors=True)
        await state.clear()
        return

    session_path = files[index]
    
    # Telethon requires the path without the .session extension
    session_name = session_path[:-8] if session_path.endswith(".session") else session_path
    
    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")
    
    try:
        client = TelegramClient(session_name, api_id, api_hash)
        await client.connect()
        
        if not await client.is_user_authorized():
            await client.disconnect()
            await state.update_data(current_index=index + 1)
            return await trigger_next_session_read(chat_id, state) # Skip dead session

        me = await client.get_me()
        phone = me.phone
        await client.disconnect()

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Get code", callback_data="rs_getcode")],
            [InlineKeyboardButton(text="Skip", callback_data="rs_skip")]
        ])

        await bot.send_message(
            chat_id,
            f"📱 <b>Number</b> - +{phone}\n\nSend code?",
            parse_mode="HTML",
            reply_markup=kb
        )

    except Exception as e:
        await state.update_data(current_index=index + 1)
        return await trigger_next_session_read(chat_id, state)


@dp.message(StateFilter(ReadSessionFSM.waiting_for_zip), F.document)
async def process_zip_file(msg: Message, state: FSMContext):
    if not msg.document.file_name.endswith('.zip'):
        return await msg.answer("❌ Please send a valid .zip file.")

    status_msg = await msg.answer("🔄 <i>Downloading and extracting zip...</i>", parse_mode="HTML")
    
    # Setup temp directories
    extract_dir = f"temp_sessions/extract_{msg.from_user.id}_{int(time.time())}"
    os.makedirs(extract_dir, exist_ok=True)
    zip_path = f"{extract_dir}/archive.zip"
    
    await bot.download(msg.document, destination=zip_path)
    
    try:
        shutil.unpack_archive(zip_path, extract_dir)
        os.remove(zip_path) # Remove original zip
    except Exception as e:
        shutil.rmtree(extract_dir, ignore_errors=True)
        return await status_msg.edit_text("❌ Failed to extract the zip file.")

    # Find all .session files recursively
    session_files = glob.glob(f"{extract_dir}/**/*.session", recursive=True)
    
    if not session_files:
        shutil.rmtree(extract_dir, ignore_errors=True)
        return await status_msg.edit_text("❌ No .session files found inside the zip.")

    await status_msg.delete()
    await state.update_data(session_files=session_files, current_index=0, extract_dir=extract_dir)
    await trigger_next_session_read(msg.chat.id, state)


@dp.callback_query(F.data == "rs_skip")
async def rs_skip_callback(cq: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = data.get("current_index", 0)
    await cq.message.edit_reply_markup(reply_markup=None) # Remove buttons
    await cq.answer("Skipped")
    
    await state.update_data(current_index=index + 1)
    await trigger_next_session_read(cq.message.chat.id, state)


@dp.callback_query(F.data == "rs_getcode")
async def rs_getcode_callback(cq: CallbackQuery, state: FSMContext):
    await cq.answer("Fetching OTP...")
    await cq.message.edit_reply_markup(reply_markup=None) # Remove buttons
    
    data = await state.get_data()
    files = data.get("session_files", [])
    index = data.get("current_index", 0)
    
    session_path = files[index]
    session_name = session_path[:-8] if session_path.endswith(".session") else session_path
    
    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")
    client = TelegramClient(session_name, api_id, api_hash)
    
    code = None
    try:
        await client.connect()
        # Look for official telegram messages
        async for message in client.iter_messages(777000, limit=10):
            if message.message and "Login code:" in message.message:
                match = re.search(r"Login code:\s*(\d{5})", message.message)
                if match:
                    code = match.group(1)
                    break
    except Exception as e:
        print(f"Error fetching code: {e}")
    finally:
        await client.disconnect()

    original_text = cq.message.html_text
    if code:
        await cq.message.edit_text(f"{original_text}\n\n✅ <b>OTP:</b> <code>{code}</code>", parse_mode="HTML")
    else:
        await cq.message.edit_text(f"{original_text}\n\n❌ <b>No OTP found in recent messages.</b>", parse_mode="HTML")

    # Move to the next session
    await state.update_data(current_index=index + 1)
    await trigger_next_session_read(cq.message.chat.id, state)

async def cleanup_file(file_path: str, delay: int):
    """Background task to delete a file after a specified delay."""
    await asyncio.sleep(delay)
    if os.path.exists(file_path):
        os.remove(file_path)

@dp.message(StateFilter(CreateSessionFSM.waiting_number))
async def create_session_number(msg: Message, state: FSMContext):
    phone = msg.text.strip()
    
    os.makedirs("temp_sessions", exist_ok=True)
    session_name = f"temp_sessions/sess_{msg.from_user.id}_{int(time.time())}"
    
    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")
    
    # Create file-backed SQLite session
    client = TelegramClient(session_name, api_id, api_hash)
    
    try:
        await client.connect()
        sent = await client.send_code_request(phone)
        await msg.answer("📩 Code sent! Please enter the OTP you received:")
        
        await state.update_data(
            session_name=session_name, 
            phone=phone, 
            phone_code_hash=sent.phone_code_hash
        )
        await state.set_state(CreateSessionFSM.waiting_otp)
    except Exception as e:
        await msg.answer(f"❌ Failed to send code: {e}")
    finally:
        await client.disconnect()


@dp.message(StateFilter(CreateSessionFSM.waiting_otp))
async def create_session_otp(msg: Message, state: FSMContext):
    data = await state.get_data()
    phone = data["phone"]
    session_name = data["session_name"]
    phone_code_hash = data["phone_code_hash"]
    code = msg.text.strip()

    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")
    client = TelegramClient(session_name, api_id, api_hash)

    try:
        await client.connect()
        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
        await finalize_create_session(msg, state, client, session_name)
    except SessionPasswordNeededError:
        await msg.answer("🔐 Two-step verification enabled. Send your 2FA password:")
        await state.set_state(CreateSessionFSM.waiting_pass)
    except Exception as e:
        await msg.answer(f"❌ Error verifying OTP: {e}")
    finally:
        if client.is_connected():
            await client.disconnect()


@dp.message(StateFilter(CreateSessionFSM.waiting_pass))
async def create_session_pass(msg: Message, state: FSMContext):
    data = await state.get_data()
    session_name = data["session_name"]
    password = msg.text.strip()

    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")
    client = TelegramClient(session_name, api_id, api_hash)

    try:
        await client.connect()
        await client.sign_in(password=password)
        await finalize_create_session(msg, state, client, session_name)
    except Exception as e:
        await msg.answer(f"❌ Error verifying password: {e}")
    finally:
        if client.is_connected():
            await client.disconnect()


async def finalize_create_session(msg: Message, state: FSMContext, client: TelegramClient, session_name: str):
    """Called when successfully logged in. Sends the .session file to the user."""
    # Ensure SQLite flushes everything by disconnecting properly
    if client.is_connected():
        await client.disconnect()

    session_file_path = f"{session_name}.session"
    
    if os.path.exists(session_file_path):
        document = FSInputFile(session_file_path)
        await msg.answer_document(
            document,
            caption="✅ <b>Session created!</b>\n\n"
                    "Forward this file to Saved Messages as it will be deleted from servers in 5 minutes.",
            parse_mode="HTML"
        )
        
        # Schedule the physical file deletion from local storage in 5 minutes
        asyncio.create_task(cleanup_file(session_file_path, 300))
    else:
        await msg.answer("❌ Error: Session file could not be found.")

    # Provide next actions
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Cancel", callback_data="cancel_create")]
    ])
    await msg.answer("➕ Send another number or press Cancel", reply_markup=kb)
    await state.set_state(CreateSessionFSM.waiting_number)


@dp.callback_query(F.data == "cancel_create")
async def cancel_create_callback(cq: CallbackQuery, state: FSMContext):
    await state.clear()
    await cq.answer("Session creation cancelled.")
    await cq.message.edit_text("✅ <b>Session creation cancelled.</b>\nPress /start to return home.", parse_mode="HTML")



# --- Main Admin Add ---
@dp.message(Command("add"))
async def cmd_add_start(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id): return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Manual 📱", callback_data="add_type_manual")],
        [InlineKeyboardButton(text="Bulk ZIP 📂", callback_data="add_type_bulk")],
        [InlineKeyboardButton(text="Back 🔙", callback_data="admin_back")]
    ])
    await msg.answer("🛠️ <b>Choose Addition Method:</b>", parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data == "add_type_bulk")
async def bulk_start(cq: CallbackQuery, state: FSMContext):
    await cq.message.edit_text("📂 <b>Send Session ZIP</b>\nUpload a zip containing <code>.session</code> files.", parse_mode="HTML")
    await state.set_state(BulkAddSession.waiting_for_zip)

@dp.message(StateFilter(BulkAddSession.waiting_for_zip), F.document)
async def bulk_zip_receive(msg: Message, state: FSMContext):
    if not msg.document.file_name.endswith('.zip'):
        return await msg.answer("❌ Send a ZIP file.")
    
    status = await msg.answer("⏳ <i>Extracting...</i>", parse_mode="HTML")
    path = f"temp_bulk/{msg.from_user.id}_{int(time.time())}"
    os.makedirs(path, exist_ok=True)
    zip_f = f"{path}/s.zip"
    await bot.download(msg.document, destination=zip_f)
    shutil.unpack_archive(zip_f, path)
    
    files = glob.glob(f"{path}/**/*.session", recursive=True)
    if not files:
        shutil.rmtree(path)
        return await status.edit_text("❌ No sessions found.")
    
    await state.update_data(session_files=files, extract_dir=path)
    await status.edit_text("🔐 <b>2FA Password</b>\nType the current password for these accounts (or <code>None</code>):", parse_mode="HTML")
    await state.set_state(BulkAddSession.waiting_for_global_pass)

# --- Process Results & Show Menu ---
@dp.message(StateFilter(BulkAddSession.waiting_for_global_pass))
@dp.message(StateFilter(BulkAddSession.waiting_for_global_pass))
async def bulk_process_start(msg: Message, state: FSMContext):
    p = msg.text.strip()
    global_pass = None if p.lower() == "none" else p
    data = await state.get_data()
    files = data['session_files']
    
    results = {"working": [], "dead": []}
    status_msg = await msg.answer("🚀 <b>Verifying Sessions...</b>", parse_mode="HTML")
    
    api_id, api_hash = int(os.getenv("API_ID")), os.getenv("API_HASH")
    
    for i, path in enumerate(files):
        if i % 5 == 0:
            await status_msg.edit_text(
                f"🔄 <b>Checking Sessions...</b>\n"
                f"{get_prog_bar(i, len(files))}\n"
                f"🟢 Working: {len(results['working'])}"
            )
        
        fix_telethon_session(path)
        client = TelegramClient(path.replace(".session", ""), api_id, api_hash)
        try:
            await client.connect()
            if await client.is_user_authorized():
                results["working"].append(path)
            else:
                results["dead"].append(path)
        except:
            results["dead"].append(path)
        finally:
            await client.disconnect()

    await state.update_data(results=results, global_pass=global_pass)
    
    # Show country selection immediately for working accounts
    kb = InlineKeyboardBuilder()
    for c in countries_col.find({}):
        kb.button(text=c['name'], callback_data=f"fbulk:{c['name']}")
    kb.adjust(2)
    
    await status_msg.edit_text(
        f"✅ <b>Scan Complete</b>\n🟢 Working: {len(results['working'])}\n💀 Dead: {len(results['dead'])}\n\n"
        f"🌍 <b>Select Country to add working stocks to:</b>", 
        reply_markup=kb.as_markup(), 
        parse_mode="HTML"
    )
    await state.set_state(BulkAddSession.viewing_results)

async def show_bulk_menu(msg: Message, res):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Add All Working", callback_data="assign_healthy"),
         InlineKeyboardButton(text="❌ Cancel", callback_data="admin_back")]
    ])
    text = (f"✅ <b>Scan Complete</b>\n\n🟢 Working: {len(res['working'])}\n"
            f"💀 Dead: {len(res['dead'])}")
    await msg.edit_text(text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data == "bulk_rm_2fa")
@dp.callback_query(F.data.startswith("assign_"))
async def bulk_assign_country(cq: CallbackQuery, state: FSMContext):
    await state.update_data(atype=cq.data.split("_")[1])
    
    # Generate Country Keyboard
    kb = InlineKeyboardBuilder()
    for c in countries_col.find({}):
        kb.button(text=c['name'], callback_data=f"fbulk:{c['name']}")
    kb.adjust(2)
    
    # Send a NEW message for country selection
    await cq.message.answer(
        "🌍 <b>Select Country:</b>\n<i>The accounts will be saved under this category.</i>", 
        reply_markup=kb.as_markup(), 
        parse_mode="HTML"
    )
    await cq.answer()

@dp.callback_query(F.data.startswith("fbulk:"))
async def bulk_final_save(cq: CallbackQuery, state: FSMContext):
    country = cq.data.split(":")[1]
    data = await state.get_data()
    working_files = data['results']['working']
    gpass = data.get('global_pass')
    
    await cq.message.edit_text(f"💾 Saving {len(working_files)} accounts to {country}...")
    
    success = 0
    for path in working_files:
        try:
            phone_match = re.search(r'\d+', os.path.basename(path))
            phone = phone_match.group() if phone_match else f"unknown_{int(time.time())}_{success}"
            
            save_session_to_db(phone, path.replace(".session", ""), country, "active", gpass)
            success += 1
        except Exception as e: pass

    # Clean up temp files
    shutil.rmtree(data['extract_dir'], ignore_errors=True)
    await cq.message.edit_text(f"✅ <b>Done!</b> Added {success} working accounts to {country}.", parse_mode="HTML")
    await state.clear()

@dp.callback_query(F.data.startswith("assign_"))
async def bulk_assign_country(cq: CallbackQuery, state: FSMContext):
    await state.update_data(atype=cq.data.split("_")[1])
    
    # Generate Country Keyboard
    kb = InlineKeyboardBuilder()
    for c in countries_col.find({}):
        kb.button(text=c['name'], callback_data=f"fbulk:{c['name']}")
    kb.adjust(2)
    
    # We send a NEW message here instead of editing cq.message
    await cq.message.answer(
        "🌍 <b>Select Country:</b>\n<i>The accounts will be saved under this category.</i>", 
        reply_markup=kb.as_markup(), 
        parse_mode="HTML"
    )
    await cq.answer()

@dp.callback_query(F.data.startswith("fbulk:"))
async def bulk_final_save(cq: CallbackQuery, state: FSMContext):
    country = cq.data.split(":")[1]
    data = await state.get_data()
    atype, res, gpass = data['atype'], data['results'], data.get('global_pass')
    
    to_add = []
    if atype == "healthy": 
        to_add = [(p, "healthy") for p in res['healthy']]
    else: 
        for k in ["healthy", "temp_spam", "perm_spam", "frozen"]:
            to_add.extend([(p, k) for p in res[k]])

    # Edit the country-selection message to show progress
    await cq.message.edit_text(f"💾 <b>Saving {len(to_add)} accounts to {country}...</b>", parse_mode="HTML")
    
    added = 0
    for path, status in to_add:
        client = TelegramClient(path.replace(".session", ""), int(os.getenv("API_ID")), os.getenv("API_HASH"))
        try:
            await client.connect()
            me = await client.get_me()
            await client.disconnect()
            # Save to DB logic
            save_session_to_db(me.phone, path.replace(".session", ""), country, status, gpass)
            added += 1
        except Exception as e:
            print(f"Failed to save {path}: {e}")
    
    # Final confirmation in the same message
    await cq.message.edit_text(f"✅ <b>Success!</b>\nAdded {added} accounts to the <b>{country}</b> database.")
    
    # Cleanup temp files
    if 'extract_dir' in data:
        shutil.rmtree(data['extract_dir'], ignore_errors=True)
    
    await state.clear()


# ================= Manual Add Flow =================

# --- Helper for checking a single account ---
async def single_check_acc(session_path: str, api_id: int, api_hash: str) -> str:
    """Checks a single account via @spambot and returns its status."""
    client = TelegramClient(session_path, api_id, api_hash)
    status = "dead"
    try:
        await client.connect()
        if not await client.is_user_authorized():
            return "dead"
        
        async with client.conversation("@spambot", timeout=10) as conv:
            await conv.send_message("/start")
            reply = (await conv.get_response()).message
        
        if "Good news" in reply: status = "healthy"
        elif "unfortunately, some numbers" in reply: status = "healthy"
        elif "I’m very sorry" in reply: status = "temp_spam"
        elif "Your account was blocked" in reply: status = "frozen"
        elif "I’m afraid" in reply: status = "perm_spam"
        else: status = "temp_spam"
    except Exception as e:
        print(f"Manual Check Error: {e}")
        status = "dead"
    finally:
        await client.disconnect()
    return status

# --- 1. Start: Select Country ---
@dp.callback_query(F.data == "add_type_manual")
async def manual_add_start(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    
    kb = InlineKeyboardBuilder()
    for c in countries_col.find({}):
        kb.button(text=c['name'], callback_data=f"madd_c:{c['name']}")
    kb.adjust(2)
    kb.row(InlineKeyboardButton(text="🔙 Back", callback_data="admin_back"))
    
    await cq.message.edit_text(
        "🌍 <b>Select Country for Manual Addition:</b>\n"
        "<i>The generated session will be stored under this category.</i>", 
        reply_markup=kb.as_markup(), 
        parse_mode="HTML"
    )
    await state.set_state(ManualAddFSM.waiting_country)

# --- 2. Country Selected: Ask for Number ---
@dp.callback_query(StateFilter(ManualAddFSM.waiting_country), F.data.startswith("madd_c:"))
async def manual_add_country_selected(cq: CallbackQuery, state: FSMContext):
    country_name = cq.data.split(":")[1]
    await state.update_data(country=country_name)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="admin_back")]])
    await cq.message.edit_text(
        f"📱 <b>Country:</b> {country_name}\n\n"
        "Send the <b>Phone Number</b> with country code (e.g., <code>+14151234567</code>):",
        parse_mode="HTML",
        reply_markup=kb
    )
    await state.set_state(ManualAddFSM.waiting_number)

# --- 3. Number Received: Send Code ---
@dp.message(StateFilter(ManualAddFSM.waiting_number))
async def manual_add_process_number(msg: Message, state: FSMContext):
    phone = msg.text.strip()
    
    os.makedirs("temp_sessions", exist_ok=True)
    session_path = f"temp_sessions/madd_{msg.from_user.id}_{int(time.time())}"
    
    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")
    client = TelegramClient(session_path, api_id, api_hash)
    
    status_msg = await msg.answer("🔄 <i>Requesting code from Telegram...</i>", parse_mode="HTML")
    
    try:
        await client.connect()
        sent = await client.send_code_request(phone)
        
        await state.update_data(
            session_path=session_path,
            phone=phone,
            phone_code_hash=sent.phone_code_hash,
            password="None"
        )
        
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="admin_back")]])
        await status_msg.edit_text(f"📩 <b>Code sent to {phone}!</b>\n\nPlease enter the OTP:", parse_mode="HTML", reply_markup=kb)
        await state.set_state(ManualAddFSM.waiting_otp)
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Failed to send code:\n<code>{e}</code>", parse_mode="HTML")
        await state.clear()
    finally:
        await client.disconnect()

# --- 4. OTP Received: Authenticate ---
@dp.message(StateFilter(ManualAddFSM.waiting_otp))
async def manual_add_process_otp(msg: Message, state: FSMContext):
    data = await state.get_data()
    phone = data["phone"]
    session_path = data["session_path"]
    phone_code_hash = data["phone_code_hash"]
    code = msg.text.strip()

    status_msg = await msg.answer("🔄 <i>Verifying code...</i>", parse_mode="HTML")
    
    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")
    client = TelegramClient(session_path, api_id, api_hash)

    try:
        await client.connect()
        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
        await finalize_manual_auth(status_msg, state, client, session_path)
    except SessionPasswordNeededError:
        await status_msg.edit_text("🔐 <b>Two-Step Verification Enabled.</b>\nSend the 2FA password:", parse_mode="HTML")
        await state.set_state(ManualAddFSM.waiting_pass)
    except Exception as e:
        await status_msg.edit_text(f"❌ Error verifying OTP:\n<code>{e}</code>", parse_mode="HTML")
        await state.clear()
    finally:
        if client.is_connected():
            await client.disconnect()

# --- 5. Password Received (If 2FA) ---
@dp.message(StateFilter(ManualAddFSM.waiting_pass))
async def manual_add_process_pass(msg: Message, state: FSMContext):
    password = msg.text.strip()
    await state.update_data(password=password)
    
    data = await state.get_data()
    session_path = data["session_path"]
    
    status_msg = await msg.answer("🔄 <i>Verifying password...</i>", parse_mode="HTML")
    
    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")
    client = TelegramClient(session_path, api_id, api_hash)

    try:
        await client.connect()
        await client.sign_in(password=password)
        await finalize_manual_auth(status_msg, state, client, session_path)
    except Exception as e:
        await status_msg.edit_text(f"❌ Error verifying password:\n<code>{e}</code>", parse_mode="HTML")
        await state.clear()
    finally:
        if client.is_connected():
            await client.disconnect()

# --- 6. Post-Auth: Spam Check & Actions Menu ---
async def finalize_manual_auth(msg: Message, state: FSMContext, client: TelegramClient, session_path: str):
    await client.disconnect() 
    
    data = await state.get_data()
    phone = data["phone"]
    country = data["country"]
    password = data.get("password", "None")

    # Save directly to DB without running @spambot check
    save_session_to_db(
        phone=phone, 
        session_path=session_path,
        country=country, 
        status="active",
        password=password
    )
    
    if os.path.exists(f"{session_path}.session"):
        os.remove(f"{session_path}.session")
        
    await msg.edit_text(f"✅ <b>Account +{phone} added directly to {country} stock!</b>", parse_mode="HTML")
    await state.clear()


@dp.message(Command("addcountry"))
# ===== Admin Country Commands =====
@dp.message(Command("addcountry"))
async def cmd_add_country(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id): return
    await msg.answer(
        "🌍 <b>Add Country</b>\n\n"
        "Send the country details in this format:\n"
        "<code>CountryName, Price</code>\n\n"
        "<i>Example: India, 50</i>", parse_mode="HTML"
    )
    await state.set_state(AddCountryFSM.waiting_data)

@dp.message(StateFilter(AddCountryFSM.waiting_data))
async def handle_add_country(msg: Message, state: FSMContext):
    parts = [p.strip() for p in msg.text.split(",")]
    if len(parts) != 2:
        return await msg.answer("❌ Invalid format. Need exactly 2 values (Country, Price).")
    
    try:
        name = parts[0]
        price = float(parts[1])
    except ValueError:
        return await msg.answer("❌ Invalid price format. Use numbers.")

    countries_col.update_one(
        {"name": name}, 
        {"$set": {
            "price": price,
            "stock": 0
        }}, 
        upsert=True
    )
    await msg.answer(f"✅ Country <b>{name}</b> added with a flat price of {fmt_curr(price)}.", parse_mode="HTML")
    await state.clear()


# ================= /sc Command (Spam Check & Sorter) =================

async def cmd_spam_check_sorter(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("🔍 <b>Spam Checker & Sorter</b>\n\nUpload a <code>.zip</code> containing your sessions. The bot will categorize them into Healthy, Spam, and Freeze files.", parse_mode="HTML")
    await state.set_state(SpamCheckSorterFSM.waiting_for_zip)

@dp.callback_query(F.data == "sc_start")
async def cb_sc_start(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    await state.clear()
    await cq.message.edit_text("🔍 <b>Spam Checker & Sorter</b>\n\nUpload a <code>.zip</code> containing your sessions. The bot will categorize them into Healthy, Spam, and Freeze files.", parse_mode="HTML")
    await state.set_state(SpamCheckSorterFSM.waiting_for_zip)

@dp.message(StateFilter(SpamCheckSorterFSM.waiting_for_zip), F.document)
async def process_sc_zip(msg: Message, state: FSMContext):
    if not msg.document.file_name.endswith('.zip'):
        return await msg.answer("❌ Please upload a valid .zip archive.")

    status_msg = await msg.answer("🔄 <i>Extracting archive for analysis...</i>", parse_mode="HTML")
    
    base_dir = f"temp_sc/job_{msg.from_user.id}_{int(time.time())}"
    extract_dir = f"{base_dir}/extracted"
    out_dir = f"{base_dir}/sorted"
    
    os.makedirs(extract_dir, exist_ok=True)
    os.makedirs(f"{out_dir}/Healthy", exist_ok=True)
    os.makedirs(f"{out_dir}/Spam", exist_ok=True)
    os.makedirs(f"{out_dir}/Freeze", exist_ok=True)
    os.makedirs(f"{out_dir}/Dead", exist_ok=True)

    zip_path = f"{base_dir}/upload.zip"
    await bot.download(msg.document, destination=zip_path)
    
    try:
        shutil.unpack_archive(zip_path, extract_dir)
        os.remove(zip_path)
    except Exception:
        shutil.rmtree(base_dir, ignore_errors=True)
        return await status_msg.edit_text("❌ Failed to extract ZIP.")

    files = glob.glob(f"{extract_dir}/**/*.session", recursive=True)
    if not files:
        shutil.rmtree(base_dir, ignore_errors=True)
        return await status_msg.edit_text("❌ No .session files found.")

    api_id, api_hash = int(os.getenv("API_ID")), os.getenv("API_HASH")
    counts = {"Healthy": 0, "Spam": 0, "Freeze": 0, "Dead": 0}

    for idx, fpath in enumerate(files):
        if idx % 5 == 0:
            await status_msg.edit_text(f"🔍 <b>Sorting Sessions...</b>\n{get_prog_bar(idx, len(files))}\nProcessed: {idx}/{len(files)}", parse_mode="HTML")
        
        fix_telethon_session(fpath)
        client = TelegramClient(fpath.replace(".session", ""), api_id, api_hash)
        file_name = os.path.basename(fpath)
        category = "Dead"
        
        try:
            await client.connect()
            if await client.is_user_authorized():
                async with client.conversation("@spambot", timeout=10) as conv:
                    await conv.send_message("/start")
                    reply = (await conv.get_response()).message
                
                if "Good news" in reply or "some phone numbers may trigger" in reply:
                    category = "Healthy"
                elif "Your account was blocked" in reply:
                    category = "Freeze"
                elif "I\u2019m very sorry" in reply or "I\u2019m afraid" in reply:
                    category = "Spam"
                else:
                    category = "Spam"
        except Exception:
            category = "Dead"
        finally:
            if client.is_connected():
                await client.disconnect()

        # Move the file to its categorized folder
        shutil.move(fpath, f"{out_dir}/{category}/{file_name}")
        counts[category] += 1

    await status_msg.edit_text("📦 <i>Zipping categorized folders...</i>", parse_mode="HTML")

    # Zip and send each populated category
    for cat in ["Healthy", "Spam", "Freeze"]:
        if counts[cat] > 0:
            cat_zip = f"{base_dir}/{cat}_Sessions.zip"
            shutil.make_archive(cat_zip.replace('.zip', ''), 'zip', f"{out_dir}/{cat}")
            await msg.answer_document(
                document=FSInputFile(cat_zip),
                caption=f"✅ <b>{cat} Accounts</b>\nTotal: {counts[cat]}",
                parse_mode="HTML"
            )

    await status_msg.delete()
    await msg.answer("🏁 <b>Spam Check Completed.</b>\nUse the Healthy zip with the /add command.", parse_mode="HTML")

    # Cleanup temp directory
    shutil.rmtree(base_dir, ignore_errors=True)
    await state.clear()
SESS_COUNTRIES_PER_PAGE = 8
async def send_session_country_menu(cq: CallbackQuery, page: int = 0):
    await cq.answer()
    
    countries = list(countries_col.find({}))
    total = len(countries)
    
    if total == 0:
        kb = InlineKeyboardBuilder()
        kb.button(text="▪️ Back", callback_data="sbsessions")
        return await cq.message.edit_text("❌ No session countries available.", reply_markup=kb.as_markup())

    total_pages = math.ceil(total / SESS_COUNTRIES_PER_PAGE)
    page = max(0, min(page, total_pages - 1))
    start = page * SESS_COUNTRIES_PER_PAGE
    end = start + SESS_COUNTRIES_PER_PAGE
    paginated = countries[start:end]

    kb = InlineKeyboardBuilder()
    
    for c in paginated:
        kb.button(text=html.escape(c["name"]), callback_data=f"sess_country:{c['name']}")
    kb.adjust(2)

    nav_row = []
    start_page = max(0, page - 2)
    end_page = min(total_pages, start_page + 5)
    
    for p in range(start_page, end_page):
        label = f"[{p+1}]" if p == page else str(p+1)
        nav_row.append(InlineKeyboardButton(text=label, callback_data=f"sess_page:{p}"))
    
    kb.row(*nav_row)
    kb.row(
        InlineKeyboardButton(text="🔍 Search", callback_data="sess_search"),
        InlineKeyboardButton(text="▪️ Back", callback_data="sbsessions")
    )

    text = (
        f"🗂 <b>Countries currently in Stock-(sessions)</b>\n"
        f"––––––––––––––————––•\n"
        f"• <u>All sessions are spam free 100%</u>\n"
        f"• <u>Advanced, secure extraction</u>\n"
        f"• <u>Execution time 5-To-12 minute</u>\n"
        f"• <u>Maximum 3000, Minimum 5</u>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖"
    )

    await cq.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "buy_sessions")
async def callback_buy_sessions_start(cq: CallbackQuery, state: FSMContext):
    await state.clear()
    await send_session_country_menu(cq, page=0)

@dp.callback_query(F.data.startswith("sess_page:"))
async def sess_paginate_countries(cq: CallbackQuery):
    page = int(cq.data.split(":")[1])
    await send_session_country_menu(cq, page)


# ================= 2. 2FA Selection =================
@dp.callback_query(F.data.startswith("sess_country:"))
async def callback_sess_country(cq: CallbackQuery):
    await cq.answer()
    _, country_name = cq.data.split(":", 1)
    
    country = countries_col.find_one({"name": country_name})
    if not country:
        return await cq.answer("❌ Country not found.", show_alert=True)

    total_avail = country.get('stock_healthy', 0) + country.get('stock_temp_spam', 0)
    
    text = (
        f"<b>How do you want the Password-(2FA)</b>\n"
        f"––––––––––––––————––•\n"
        f"<b><u>Country</u></b>   → {country_name}\n"
        f"<b><u>Available</u></b> → {total_avail} SESSION\n\n"
        f"<b><u>Price list</u>:</b>\n"
        f"Healthy - {fmt_curr(country.get('price_healthy', 0))}\n"
        f"Spam - {fmt_curr(country.get('price_temp_spam', 0))}\n"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Disable 2FA", callback_data=f"sess_2fa:{country_name}:disable")],
        [InlineKeyboardButton(text="Enable 2FA", callback_data=f"sess_2fa:{country_name}:enable")],
        [InlineKeyboardButton(text="▪️ Back", callback_data="buy_sessions")]
    ])
    
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb)


# ================= 3. Condition Selection =================
@dp.callback_query(F.data.startswith("sess_2fa:"))
async def callback_sess_2fa(cq: CallbackQuery):
    await cq.answer()
    _, country_name, twofa_type = cq.data.split(":")
    
    country = countries_col.find_one({"name": country_name})
    
    healthy_stock = country.get('stock_healthy', 0)
    spam_stock = country.get('stock_temp_spam', 0)
    healthy_price = country.get('price_healthy', 0)
    spam_price = country.get('price_temp_spam', 0)

    text = (
        f"<b>Which condition you wanna buy</b>\n"
        f"––––––––––––––————––•\n"
        f"🟢 <u>Healthy</u> - {healthy_stock} sessions - {fmt_curr(healthy_price)}\n"
        f"🟡 <u>Spam</u> - {spam_stock} sessions - {fmt_curr(spam_price)}\n"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Healthy", callback_data=f"sess_cond:{country_name}:{twofa_type}:healthy")],
        [InlineKeyboardButton(text="Spam", callback_data=f"sess_cond:{country_name}:{twofa_type}:temp_spam")],
        [InlineKeyboardButton(text="▪️ Back", callback_data=f"sess_country:{country_name}")]
    ])
    
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb)


# ================= 4. Quantity Numpad Rendering =================
async def render_sess_numpad(cq: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    qty_str = data.get("qty", "0")
    qty = int(qty_str) if qty_str else 0
    
    country_name = data['country']
    condition = data['condition']
    
    country = countries_col.find_one({"name": country_name})
    price_per = country.get(f"price_{condition}", 0)
    available = country.get(f"stock_{condition}", 0)
    
    total_price = qty * price_per
    key_code = f"[SES-{country_name[:3].upper()}]"

    text = (
        f"<b>How sessions do you want buy-(SES)</b>\n"
        f"––––––––––––––————––•\n"
        f"<b><u>Country</u></b>  →  {country_name}\n"
        f"<b><u>Condition</u></b> - {condition.replace('_', ' ').title()}\n"
        f"<b><u>Key-code</u></b>   →  {key_code}\n"
        f"<b><u>Available</u></b>   →  {available} SESSION\n"
        f"<b><u>Price</u></b>  →  {fmt_curr(price_per)}/each\n"
    )

    kb = InlineKeyboardBuilder()
    
    # Live Status Row
    kb.row(InlineKeyboardButton(text=f"SES: {qty} | Total: {fmt_curr(total_price)}", callback_data="ignore"))
    
    # Numpad Rows
    kb.row(
        InlineKeyboardButton(text="1", callback_data="sess_num:1"),
        InlineKeyboardButton(text="2", callback_data="sess_num:2"),
        InlineKeyboardButton(text="3", callback_data="sess_num:3")
    )
    kb.row(
        InlineKeyboardButton(text="4", callback_data="sess_num:4"),
        InlineKeyboardButton(text="5", callback_data="sess_num:5"),
        InlineKeyboardButton(text="6", callback_data="sess_num:6")
    )
    kb.row(
        InlineKeyboardButton(text="7", callback_data="sess_num:7"),
        InlineKeyboardButton(text="8", callback_data="sess_num:8"),
        InlineKeyboardButton(text="9", callback_data="sess_num:9")
    )
    kb.row(
        InlineKeyboardButton(text="Buy ✅", callback_data="sess_buy_confirm"),
        InlineKeyboardButton(text="0", callback_data="sess_num:0"),
        InlineKeyboardButton(text="⌫", callback_data="sess_num:del")
    )
    
    # Back Button
    kb.row(InlineKeyboardButton(text="🔙 Back", callback_data=f"sess_2fa:{country_name}:{data['twofa']}"))

    try:
        await cq.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    except Exception:
        pass # Ignore message not modified errors

@dp.callback_query(F.data.startswith("sess_cond:"))
async def callback_sess_cond(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    _, country_name, twofa_type, condition = cq.data.split(":")
    
    await state.update_data(
        country=country_name,
        twofa=twofa_type,
        condition=condition,
        qty="0"
    )
    await state.set_state(BuySessionFlow.waiting_for_quantity)
    await render_sess_numpad(cq, state)

@dp.callback_query(StateFilter(BuySessionFlow.waiting_for_quantity), F.data.startswith("sess_num:"))
async def callback_sess_numpad(cq: CallbackQuery, state: FSMContext):
    val = cq.data.split(":")[1]
    data = await state.get_data()
    current = data.get("qty", "0")
    
    if val == "del":
        current = current[:-1] if len(current) > 1 else "0"
    else:
        current = val if current == "0" else current + val
        
    if int(current) > 3000:
        current = "3000"
        await cq.answer("⚠️ Maximum limit is 3000", show_alert=True)
        
    await state.update_data(qty=current)
    await render_sess_numpad(cq, state)
    await cq.answer()


# ================= 5. Confirmation & Terms =================
@dp.callback_query(StateFilter(BuySessionFlow.waiting_for_quantity), F.data == "sess_buy_confirm")
async def callback_sess_buy_confirm(cq: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    qty = int(data.get("qty", "0"))
    
    if qty < 4:
        return await cq.answer("⚠️ Minimum limit is 4 sessions", show_alert=True)

    country = countries_col.find_one({"name": data['country']})
    user = users_col.find_one({"_id": cq.from_user.id})
    
    price_per = country.get(f"price_{data['condition']}", 999999)
    total_price = qty * price_per
    available = country.get(f"stock_{data['condition']}", 0)
    user_bal = user.get("balance", 0.0)
    
    if qty > available:
        return await cq.answer(f"⚠️ Only {available} sessions currently in stock!", show_alert=True)
        
    if user_bal < total_price:
        return await cq.answer(f"❌ Insufficient Balance! You need {fmt_curr(total_price)}.", show_alert=True)

    terms_text = (
        f"⚠️ <b>Session Buying Terms</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"• <b><u>Sessions</u>:</b> {qty}x {data['country']} ({data['condition'].title()})\n"
        f"• <b><u>2FA Action</u>:</b> {data['twofa'].title()} 2FA\n"
        f"• <b><u>Total Price</u>:</b> {fmt_curr(total_price)}\n\n"
        f"<b>Do you confirm this bulk purchase?</b>"
    )

    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✅ Accept", callback_data="sess_execute_final"),
        InlineKeyboardButton(text="❌ Decline", callback_data=f"sess_cond:{data['country']}:{data['twofa']}:{data['condition']}")
    )

    await cq.message.edit_text(terms_text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await cq.answer()


# ================= 6. Execution & ZIP Delivery =================
@dp.callback_query(StateFilter(BuySessionFlow.waiting_for_quantity), F.data == "sess_execute_final")
async def callback_sess_execute(cq: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    qty = int(data.get("qty", "0"))
    country_name = data['country']
    condition = data['condition']
    twofa_type = data['twofa']
    user_id = cq.from_user.id
    
    # 1. Double check atomicity
    country = countries_col.find_one({"name": country_name})
    price_per = country.get(f"price_{condition}", 999999)
    total_price = qty * price_per
    
    sessions_docs = list(numbers_col.find({
        "country": country_name, 
        "status": condition, 
        "used": False
    }).limit(qty))
    
    if len(sessions_docs) < qty:
        return await cq.answer("⚠️ Stock depleted during checkout!", show_alert=True)
        
        user = users_col.find_one({"_id": user_id})
        if user.get("balance", 0) < total_price:
            return await cq.answer("❌ Insufficient balance.", show_alert=True)

    # --- ADD THIS BLOCK ---
    if twofa_type == "enable":
        await state.set_state(BuySessionFlow.waiting_for_2fa_password)
        await cq.message.edit_text(
            "⌨️ <b>Please type and send the 2FA password you want to set for these sessions:</b>\n\n"
            "<i>⚠️ Note: Make sure to remember this password!</i>", 
            parse_mode="HTML"
        )
        return # Stops the function here so it waits for the message
    # ----------------------

    status_msg = await cq.message.edit_text("🔄 <b>Processing 2FA and Extracting sessions...\nExecution time: 5-12 Mins...</b>", parse_mode="HTML")
    

    # 2. Execute Transactions
    users_col.update_one({"_id": user_id}, {"$inc": {"balance": -total_price}})
    
    session_ids = [s['_id'] for s in sessions_docs]
    numbers_col.update_many(
        {"_id": {"$in": session_ids}}, 
        {"$set": {"used": True, "owner_id": user_id, "buy_time": datetime.now(timezone.utc)}}
    )
    
    countries_col.update_one(
        {"name": country_name}, 
        {"$inc": {f"stock_{condition}": -qty, "stock": -qty}}
    )

    orders_col.insert_one({
        "user_id": user_id,
        "type": "bulk_sessions",
        "country": country_name,
        "quantity": qty,
        "price": total_price,
        "status": "purchased",
        "created_at": datetime.now(timezone.utc)
    })

        # 3. Process the ZIP in memory (And Disable 2FA)
    zip_buffer = io.BytesIO()
    import zipfile
    
    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for s in sessions_docs:
            phone = s.get('number', 'unknown')
            session_bin = s.get('session_file')
            
            if session_bin:
                temp_path = f"temp_sessions/buy_{phone}_{int(time.time())}"
                os.makedirs("temp_sessions", exist_ok=True)
                
                # Write to temp physical file for Telethon
                with open(f"{temp_path}.session", "wb") as f:
                    f.write(session_bin)
                
                if twofa_type == "disable":
                    try:
                        client = TelegramClient(temp_path, api_id, api_hash)
                        await client.connect()
                        if await client.is_user_authorized():
                            curr_pass = s.get("password") if s.get("password") != "None" else None
                            await client.edit_2fa(current_password=curr_pass, new_password=None)
                            # Update DB to reflect 2FA removal
                            numbers_col.update_one({"_id": s["_id"]}, {"$set": {"password": "None"}})
                        await client.disconnect()
                    except Exception as e:
                        print(f"Failed to remove 2FA for {phone}: {e}")

                # Read the updated binary back into the zip
                with open(f"{temp_path}.session", "rb") as f:
                    zf.writestr(f"{phone}.session", f.read())
                    
                if os.path.exists(f"{temp_path}.session"):
                    os.remove(f"{temp_path}.session")
                    

    # Mocking the 2FA Processing Delay as requested
    await asyncio.sleep(2) 
    
    zip_buffer.seek(0)
    zip_file = BufferedInputFile(zip_buffer.read(), filename=f"Sessions_{country_name}_{qty}.zip")

    # 4. Deliver File
    kb = InlineKeyboardBuilder()
    kb.button(text="▪️ Main Menu", callback_data="back_main")
    
    await cq.message.answer_document(
        document=zip_file,
        caption=(
            f"✅ <b>Bulk Sessions Delivered Successfully!</b>\n"
            f"––––––––––––––————––•\n"
            f"📦 <b>Amount:</b> {qty} Sessions\n"
            f"🌍 <b>Country:</b> {country_name}\n"
            f"🛡️ <b>2FA Setting:</b> {twofa_type.title()}\n"
            f"💸 <b>Total Paid:</b> {fmt_curr(total_price)}\n\n"
            f"<i>Enjoy your spam-free sessions!</i>"
        ),
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )
    
    await status_msg.delete()

# 5. Logging to Channels
    buyer_name = user.get("username") or f"User {user_id}"
    new_bal = user.get("balance", 0) - total_price

    admin_log = (
        f"<pre>📢 Bulk Session Purchase</pre>\n\n"
        f"<b>• Country:</b> {country_name}\n"
        f"<b>• Quantity:</b> {qty}\n"
        f"<b>• 2FA Req:</b> hidde•••\n"
        f"<b>• Paid:</b> {fmt_curr(total_price)}\n\n"
        f"<b>👤 User:</b> @{buyer_name} (<code>{user_id}</code>)\n"
        f"<b>💰 Rem. Balance:</b> {fmt_curr(new_bal)}"
    )
    await bot.send_message(-1004492615113, admin_log, parse_mode="HTML")

    channel_log = (
        f"<pre><u>✅ <b>New Bulk Session Sold</b></u></pre>\n\n"
        f"➖ <b><u>Country:</u></b> {country_name}\n"
        f"➖ <b><u>Quantity:</u></b> {qty} Sessions 📁\n"
        f"➖ <b><u>Application:</u> Теlegгам 🍷</b>\n\n"
        f"<b>• @tgbitz_bot || @tgbitz</b>"
    )
    await bot.send_message(-1004484806488, channel_log, parse_mode="HTML", reply_markup=buy_button)

    buy_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="• Buy Sessions Now •", url="https://t.me/tgbitz_bot?start=starting")]
    ])
    await state.clear()

    
@dp.message(StateFilter(BuySessionFlow.waiting_for_2fa_password))
async def process_custom_2fa_password(msg: Message, state: FSMContext):
    user_password = msg.text.strip()
    data = await state.get_data()
    
    qty = int(data.get("qty", "0"))
    country_name = data['country']
    condition = data['condition']
    user_id = msg.from_user.id
    
    # 1. Re-verify Stock and Balance
    country = countries_col.find_one({"name": country_name})
    price_per = country.get(f"price_{condition}", 999999)
    total_price = qty * price_per
    
    sessions_docs = list(numbers_col.find({
        "country": country_name, 
        "status": condition, 
        "used": False
    }).limit(qty))
    
    if len(sessions_docs) < qty:
        return await msg.answer("⚠️ Stock depleted during checkout! Please try again.")

    user = users_col.find_one({"_id": user_id})
    if user.get("balance", 0) < total_price:
        return await msg.answer("❌ Insufficient balance.")

    status_msg = await msg.answer("🔄 <b>Processing custom 2FA and Extracting sessions...\nExecution time: 5-12 Mins...</b>", parse_mode="HTML")

    # 2. Execute Transactions
    users_col.update_one({"_id": user_id}, {"$inc": {"balance": -total_price}})
    
    session_ids = [s['_id'] for s in sessions_docs]
    numbers_col.update_many(
        {"_id": {"$in": session_ids}}, 
        {"$set": {"used": True, "owner_id": user_id, "buy_time": datetime.now(timezone.utc)}}
    )
    
    countries_col.update_one(
        {"name": country_name}, 
        {"$inc": {f"stock_{condition}": -qty, "stock": -qty}}
    )

    orders_col.insert_one({
        "user_id": user_id,
        "type": "bulk_sessions",
        "country": country_name,
        "quantity": qty,
        "price": total_price,
        "status": "purchased",
        "created_at": datetime.now(timezone.utc)
    })

    # 3. Process Telethon 2FA Changes & ZIP
    zip_buffer = io.BytesIO()
    import zipfile
    
    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for s in sessions_docs:
            phone = s.get('number', 'unknown')
            session_bin = s.get('session_file')
            
            if session_bin:
                # Create a unique temp path for this specific session
                temp_path = f"temp_sessions/buy_{phone}_{int(time.time())}"
                os.makedirs("temp_sessions", exist_ok=True)
                
                # Write binary data from DB to a physical .session file
                with open(f"{temp_path}.session", "wb") as f:
                    f.write(session_bin)
                    
                try:
                    client = TelegramClient(temp_path, api_id, api_hash)
                    await client.connect()
                    
                    if await client.is_user_authorized():
                        # Get current password if it exists in DB
                        curr_pass = s.get("password") if s.get("password") != "None" else None
                        
                        # Apply the new 2FA password
                        await client.edit_2fa(current_password=curr_pass, new_password=user_password)
                        
                        # Update DB with the new password
                        numbers_col.update_one({"_id": s["_id"]}, {"$set": {"password": user_password}})
                            
                    await client.disconnect()
                except Exception as e:
                    print(f"Failed to set 2FA for {phone}: {e}")
                
                # Read the updated physical session (with new 2FA) back into the ZIP
                if os.path.exists(f"{temp_path}.session"):
                    with open(f"{temp_path}.session", "rb") as f:
                        zf.writestr(f"{phone}.session", f.read())
                    
                    # Cleanup: Delete temp file after adding to ZIP
                    os.remove(f"{temp_path}.session")
                else:
                    # If something went wrong, write the original binary data so the user still gets the file
                    zf.writestr(f"{phone}.session", session_bin)

    # Prepare the file for sending
    zip_buffer.seek(0)
    zip_file = BufferedInputFile(zip_buffer.read(), filename=f"Sessions_{country_name}_{qty}.zip")

    # 4. Deliver File
    kb = InlineKeyboardBuilder()
    kb.button(text="Read sessions", url="https://t.me/tgbitz_bot?start=starting")
    
    await msg.answer_document(
        document=zip_file,
        caption=(
            f"✅ <b>Bulk Sessions Delivered Successfully!</b>\n"
            f"––––––––––––––————––•\n"
            f"📦 <b>Amount:</b> {qty} Sessions\n"
            f"🌍 <b>Country:</b> {country_name}\n"
            f"🛡️ <b>Password Set:</b> <code>{user_password}</code>\n"
            f"💸 <b>Total Paid:</b> {fmt_curr(total_price)}\n\n"
            f"<i>Enjoy your spam-free sessions!</i>"
        ),
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )
    
    await status_msg.delete()
                    
    
    # 5. Log it to channels (You can copy your channel logging code from Edit 6 of the previous block here)
    # ... [Insert your channel/admin logging here] ...

    # 5. Logging to Channels
    buyer_name = user.get("username") or f"User {user_id}"
    new_bal = user.get("balance", 0) - total_price

    admin_log = (
        f"<pre>📢 Bulk Session Purchase</pre>\n\n"
        f"<b>• Country:</b> {country_name}\n"
        f"<b>• Quantity:</b> {qty}\n"
        f"<b>• 2FA Req:</b> hidde•••\n"
        f"<b>• Paid:</b> {fmt_curr(total_price)}\n\n"
        f"<b>👤 User:</b> @{buyer_name} (<code>{user_id}</code>)\n"
        f"<b>💰 Rem. Balance:</b> {fmt_curr(new_bal)}"
    )

    channel_log = (
        f"<pre><u>✅ <b>New Bulk Session Sold</b></u></pre>\n\n"
        f"➖ <b><u>Country:</u></b> {country_name}\n"
        f"➖ <b><u>Quantity:</u></b> {qty} Sessions 📁\n"
        f"➖ <b><u>Application:</u> Теlegгам 🍷</b>\n\n"
        f"<b>• @TGBITZ_bot || @TGBitz</b>"
    )

    buy_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="• Buy Sessions Now •", url="https://t.me/TGBITZ_bot?start=starting")]
    ])
    
    try:
        await bot.send_message(-1004484806488, channel_log, parse_mode="HTML", reply_markup=buy_button)
        await bot.send_message(-1004492615113, admin_log, parse_mode="HTML")
    except Exception as e:
        print(f"Log Error: {e}")

    await state.clear()


# ================= /separate Command Handler =================
@dp.message(Command("separate"))
async def cmd_separate(msg: Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_separate")]
    ])
    await msg.answer(
        "📂 <b>File Separator Utility</b>\n\n"
        "Please send the <b>.zip</b> file containing the mixed files (e.g., .session and .json).",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await state.set_state(SeparateFSM.waiting_for_zip)

# ================= Process Uploaded ZIP =================
@dp.message(StateFilter(SeparateFSM.waiting_for_zip), F.document)
async def process_separate_zip(msg: Message, state: FSMContext):
    if not msg.document.file_name.lower().endswith('.zip'):
        return await msg.answer("❌ Please upload a valid <b>.zip</b> archive.")

    status_msg = await msg.answer("🔄 <i>Analyzing zip contents...</i>", parse_mode="HTML")
    
    # Setup unique temp directory
    extract_dir = f"temp_separate/user_{msg.from_user.id}_{int(time.time())}"
    os.makedirs(extract_dir, exist_ok=True)
    zip_path = os.path.join(extract_dir, "input_archive.zip")

    try:
        # Download and extract
        await bot.download(msg.document, destination=zip_path)
        shutil.unpack_archive(zip_path, extract_dir)
        os.remove(zip_path) # Clean up the archive itself

        # Find all unique extensions
        all_files = glob.glob(f"{extract_dir}/**/*", recursive=True)
        extensions = set()
        for f in all_files:
            if os.path.isfile(f):
                ext = os.path.splitext(f)[1].lower()
                if ext: extensions.add(ext)

        if not extensions:
            shutil.rmtree(extract_dir, ignore_errors=True)
            return await status_msg.edit_text("❌ The zip file appears to be empty or contains no valid files.")

        # Save data to state
        await state.update_data(extract_dir=extract_dir, extensions=list(extensions))

        # Create buttons for each extension
        kb = InlineKeyboardBuilder()
        for ext in sorted(list(extensions)):
            kb.button(text=f"Extract {ext}", callback_data=f"ext_sep:{ext}")
        kb.adjust(2)
        kb.row(InlineKeyboardButton(text="🗑️ Cancel", callback_data="cancel_separate"))

        await status_msg.edit_text(
            f"✅ <b>Analysis Complete!</b>\n"
            f"Found {len(extensions)} different file types.\n\n"
            f"Which files do you want to extract into a new zip?",
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )
        await state.set_state(SeparateFSM.choosing_extension)

    except Exception as e:
        print(f"Separate Error: {e}")
        shutil.rmtree(extract_dir, ignore_errors=True)
        await status_msg.edit_text("❌ An error occurred while processing the zip file.")

# ================= Extension Selection & Packing =================
@dp.callback_query(F.data.startswith("ext_sep:"), StateFilter(SeparateFSM.choosing_extension))
async def callback_extract_ext(cq: CallbackQuery, state: FSMContext):
    selected_ext = cq.data.split(":")[1]
    data = await state.get_data()
    extract_dir = data.get("extract_dir")

    if not extract_dir or not os.path.exists(extract_dir):
        await cq.answer("❌ Session expired. Please try again.", show_alert=True)
        return await state.clear()

    await cq.message.edit_text(f"📦 <b>Packing all {selected_ext} files...</b>\n<i>Please wait...</i>", parse_mode="HTML")

    # Filter files by extension
    target_files = glob.glob(f"{extract_dir}/**/*{selected_ext}", recursive=True)
    
    if not target_files:
        return await cq.message.edit_text(f"❌ No files found with extension {selected_ext}")

    # Create new ZIP in memory or temp file
    output_zip_name = f"extracted_{selected_ext.replace('.', '')}.zip"
    output_zip_path = os.path.join(os.path.dirname(extract_dir), output_zip_name)
    
    try:
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in target_files:
                # Add to zip using relative path to keep structure clean
                arcname = os.path.relpath(file_path, extract_dir)
                zf.write(file_path, arcname)

        # Send to user
        final_file = FSInputFile(output_zip_path)
        await cq.message.answer_document(
            document=final_file,
            caption=f"✅ <b>Extraction Complete</b>\n\n"
                    f"📁 <b>Type:</b> {selected_ext}\n"
                    f"📄 <b>Files count:</b> {len(target_files)}\n\n"
                    f"<i>Cleaned from original zip.</i>",
            parse_mode="HTML"
        )
        await cq.message.delete()

    except Exception as e:
        print(f"Packing Error: {e}")
        await cq.message.answer("❌ Failed to create the new zip file.")
    finally:
        # Cleanup
        shutil.rmtree(extract_dir, ignore_errors=True)
        if os.path.exists(output_zip_path):
            os.remove(output_zip_path)
        await state.clear()

# ================= Cancel Handler =================
@dp.callback_query(F.data == "cancel_separate")
async def cancel_separate(cq: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data.get("extract_dir"):
        shutil.rmtree(data.get("extract_dir"), ignore_errors=True)
    await state.clear()
    await cq.message.edit_text("❌ <b>Operation cancelled.</b>", parse_mode="HTML")
    await cq.answer()
                                                                             


# ================= 1. FSM States for ZIP Generation =================

# ================= 2. Command Handler /zipper =================
@dp.message(Command("zipper"))
async def cmd_zipper(msg: Message, state: FSMContext):
    await state.clear()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗜️ Create Zip", callback_data="zipper_start")]
    ])
    
    await msg.answer(
        "<b>File-to-ZIP Compression Utility</b>\n\n"
        "Click the button below to initialize a temporary session.", 
        reply_markup=kb,
        parse_mode="HTML"
    )

# ================= 3. Callback Start Handler =================
@dp.callback_query(F.data == "zipper_start")
async def cb_zipper_start(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    await cq.message.edit_text(
        "🔢 <b>How many files are there?</b>\n"
        "Please type and send the exact number of files you intend to compress:"
    )
    await state.set_state(ZipperFSM.waiting_for_count)

# ================= 4. Number Verification Handler =================
@dp.message(StateFilter(ZipperFSM.waiting_for_count))
async def process_file_count(msg: Message, state: FSMContext):
    if not msg.text or not msg.text.isdigit() or int(msg.text) <= 0:
        return await msg.answer("❌ <b>Invalid value.</b> Please send a valid positive number:")
    
    total_files = int(msg.text)
    
    # Establish a unique user isolation sandbox directory
    session_dir = f"temp_zipper/user_{msg.from_user.id}_{int(time.time())}"
    os.makedirs(session_dir, exist_ok=True)
    
    # Cache parameters in FSM
    await state.update_data(
        total_count=total_files, 
        current_count=0, 
        files=[], 
        session_dir=session_dir
    )
    
    await msg.answer(f"📥 <b>Database configured.</b>\nPlease send or forward your files one by one (0/{total_files} received):")
    await state.set_state(ZipperFSM.waiting_for_files)

# ================= 5. Sequential File Gathering Handler =================
@dp.message(StateFilter(ZipperFSM.waiting_for_files), F.document)
async def process_incoming_files(msg: Message, state: FSMContext):
    data = await state.get_data()
    total_count = data["total_count"]
    current_count = data["current_count"]
    file_list = data["files"]
    session_dir = data["session_dir"]
    
    # Format and clean file parameters
    raw_filename = msg.document.file_name or f"file_{current_count + 1}"
    safe_filename = "".join(c for c in raw_filename if c.isalnum() or c in "._- ").strip()
    destination_path = os.path.join(session_dir, safe_filename)
    
    status_msg = await msg.answer("⏳ <i>Caching file payload...</i>")
    await bot.download(msg.document, destination=destination_path)
    await status_msg.delete()
    
    file_list.append(destination_path)
    current_count += 1
    
    await state.update_data(current_count=current_count, files=file_list)
    
    if current_count >= total_count:
        await msg.answer(
            "✅ <b>All file targets collected!</b>\n\n"
            "Please enter the desired name for your compiled ZIP archive (without <code>.zip</code> extension):"
        )
        await state.set_state(ZipperFSM.waiting_for_zip_name)
    else:
        await msg.answer(f"📥 <b>Payload accepted.</b> Send the next file ({current_count}/{total_count}):")

# Handle alternative non-document entries gracefully
@dp.message(StateFilter(ZipperFSM.waiting_for_files))
async def invalid_file_type(msg: Message):
    await msg.answer("⚠️ File unrecognized. Please send or forward the item explicitly as an uncompressed <b>Document/File</b> attachment.")

# ================= 6. ZIP Compilation & Server Scrubbing =================
@dp.message(StateFilter(ZipperFSM.waiting_for_zip_name))
async def process_zip_name(msg: Message, state: FSMContext):
    if not msg.text:
        return await msg.answer("❌ Invalid input. Provide a safe alpha-numeric name:")
    
    # Strip dangerous characters from name
    clean_name = "".join(c for c in msg.text.strip() if c.isalnum() or c in "._- ").replace(" ", "_")
    if not clean_name.endswith(".zip"):
        clean_name += ".zip"
        
    data = await state.get_data()
    file_list = data["files"]
    session_dir = data["session_dir"]
    
    status_msg = await msg.answer("🗜️ <i>Assembling ZIP archive engine... Please wait.</i>")
    zip_file_path = os.path.join(session_dir, clean_name)
    
    try:
        # Build compression tree
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in file_list:
                if os.path.exists(file_path):
                    zf.write(file_path, os.path.basename(file_path))
        
        # Dispatch archive stream to endpoint user
        delivered_archive = FSInputFile(zip_file_path)
        await msg.answer_document(
            document=delivered_archive, 
            caption=f"📦 <b>Archive Package Ready!</b>\n📄 Name: <code>{clean_name}</code>"
        )
    except Exception as e:
        await msg.answer(f"❌ <b>Process Interrupted:</b> Internal compressor failed to build file context. Details: {e}")
    finally:
        await status_msg.delete()
        
        # Absolute structural cleaning: Removes directory and deletes variables from state storage
        shutil.rmtree(session_dir, ignore_errors=True)
        await state.clear()
        
        await msg.answer("🧹 <i>Session concluded. All local cache records and state instances have been fully purged from the bot database.</i>")
        
        
        
        
        
        
        
# ================= Admin: Remove Country =================
@dp.message(Command("removecountry"))
async def cmd_remove_country(msg: Message):
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ Not authorized.")

    countries = list(countries_col.find({}))
    if not countries:
        return await msg.answer("📭 No countries to remove.")

    kb = InlineKeyboardBuilder()
    for c in countries:
        kb.button(text=c["name"], callback_data=f"removecountry:{c['name']}")
    kb.adjust(2)
    await msg.answer("🌍 Select a country to remove:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("removecountry:"))
async def callback_remove_country(cq: CallbackQuery):
    await cq.answer()
    _, country_name = cq.data.split(":", 1)

    result = countries_col.delete_one({"name": country_name})
    if result.deleted_count == 0:
        await cq.message.edit_text(f"❌ Country <b>{country_name}</b> not found.", parse_mode="HTML")
    else:
        await cq.message.edit_text(f"✅ Country <b>{country_name}</b> removed successfully.", parse_mode="HTML")

@dp.message(Command("db"))
async def cmd_db(msg: Message):
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ Not authorized.")

    countries = list(countries_col.find({}))
    if not countries:
        return await msg.answer("❌ No countries found in DB.")

    text = "📚 <b>Numbers in Database by Country:</b>\n\n"

    for c in countries:
        country_name = c["name"]
        numbers = list(numbers_col.find({"country": country_name}))
        text += f"🌍 <b>{country_name}:</b>\n"
        if numbers:
            for num in numbers:
                text += f"• {num['number']} {'✅' if num.get('used') else ''}\n"
        else:
            text += "No number\n"
        text += "\n"

    await msg.answer(text, parse_mode="HTML")



# ====================== SELL ACCOUNT FEATURE (FIXED & FULL) ======================

sell_prices_col = db["sell_prices"]

# --- FSM States ---
class SetPrices(StatesGroup):
    waiting_list = State()

class SellSession(StatesGroup):
    waiting_sell_number = State()
    waiting_sell_otp = State()
    waiting_sell_password = State()


# --- Admin Command: Set Sell Prices ---
@dp.message(Command("setprices"))
async def cmd_set_prices(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ Not authorized.")
    
    await msg.answer(
        "📋 <b>Send the price list in this format:</b>\n\n"
        "<code>+1 USA 🇺🇸 - ₹10</code>\n"
        "<code>+91 India 🇮🇳 - ₹29</code>\n"
        "<code>+232 Sierra Leone 🇸🇱 - ₹13</code>\n\n"
        "⚠️ <i>Sending a new list will overwrite the old one.</i>",
        parse_mode="HTML"
    )
    await state.set_state(SetPrices.waiting_list)


@dp.message(StateFilter(SetPrices.waiting_list))
async def handle_set_prices(msg: Message, state: FSMContext):
    text = msg.text.strip()
    
    # IMPROVED REGEX EXPLANATION:
    # (\+\d{1,4})  -> Captures country code (e.g., +1, +232)
    # \s+          -> Matches spaces
    # (.*?)        -> Captures ANY text/emoji (Country Name + Flag) non-greedily until the hyphen
    # \s*-\s* -> Matches the hyphen separator
    # ₹?           -> Matches optional Rupee symbol
    # \s* -> Optional space
    # (\d+)        -> Captures the price number
    pattern = re.compile(r"(\+\d{1,4})\s+(.*?)\s*-\s*₹?\s*(\d+)", re.MULTILINE)

    entries = pattern.findall(text)

    # 1. Validation: Don't delete old data if the new list is empty/invalid
    if not entries:
        return await msg.answer(
            "❌ <b>Invalid format detected.</b>\n\n"
            "Make sure you use the format:\n"
            "<code>+Code CountryName Flag - ₹Price</code>\n"
            "Example:\n<code>+232 Sierra Leone 🇸🇱 - 13</code>", 
            parse_mode="HTML"
        )

    # 2. Database Update: clear old data ONLY after validation passes
    sell_prices_col.delete_many({})
    
    new_data = []
    response_lines = []

    for code, name, price in entries:
        clean_name = name.strip()
        clean_price = int(price)
        
        new_data.append({
            "code": code.strip(),
            "name": clean_name,
            "price": clean_price
        })
        
        response_lines.append(f"{code} {clean_name} - ₹{clean_price}")

    # Bulk insert is faster and safer
    if new_data:
        sell_prices_col.insert_many(new_data)

    # 3. Confirmation
    formatted_list = "\n".join(response_lines)
    await msg.answer(
        f"✅ <b>Price list updated successfully!</b>\n"
        f"<i>Added {len(new_data)} countries.</i>\n\n"
        f"<pre>{formatted_list}</pre>", 
        parse_mode="HTML"
    )
    await state.clear()

# --- Callback for Sell Button ---
# ==========================================
# 💸 SELL ACCOUNT LOGIC (REWRITTEN & FIXED)
# ==========================================

# --- 1. Sell Menu ---
@dp.callback_query(F.data == "sell")
async def callback_sell(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    prices = list(sell_prices_col.find({}))
    
    if not prices:
        return await cq.message.answer("❌ <b>Sales are currently closed.</b>\nNo price list available.")

    # High UI Price List
    price_list_text = ""
    for p in prices:
        price_list_text += f"🏳️ <code>{p['code']}</code> <b>{p['name']}</b> ➜ ₹{p['price']}\n"

    text = (
        "<b>💸 SELL YOUR TELEGRAM ACCOUNT</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>📊 Current Buying Rates:</b>\n"
        f"<blockquote expandable>{price_list_text}</blockquote>\n"
        "<b>📝 Instructions:</b>\n"
        "1. Enter your number with country code.\n"
        "2. Send the OTP received.\n"
        "3. If you have a 2FA password, enter it.\n\n"
        "👇 <b>Send your number now:</b>\n"
        "<i>(Example: +14151234567)</i>"
    )

    await cq.message.answer(text, parse_mode="HTML")
    await state.set_state(SellSession.waiting_sell_number)


# --- 2. User Sends Number ---
@dp.message(StateFilter(SellSession.waiting_sell_number))
async def user_sells_number(msg: Message, state: FSMContext):
    phone = msg.text.strip().replace(" ", "")
    
    if not phone.startswith("+") or not phone[1:].isdigit():
        return await msg.answer("❌ <b>Invalid Format!</b>\nPlease start with '+' followed by digits.\n<i>Ex: +14155550199</i>")

    # Match Country and Price
    all_prices = list(sell_prices_col.find({}))
    matched = None
    for p in all_prices:
        if phone.startswith(p["code"]):
            matched = p
            break

    if not matched:
        return await msg.answer("⚠️ <b>Sorry!</b>\nWe are not buying numbers from this country at the moment.")

    country_name = matched["name"]
    price = matched["price"]

    status_msg = await msg.answer(
        f"🌍 <b>Country:</b> {country_name}\n"
        f"💰 <b>Offer Price:</b> ₹{price}\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🔄 <i>Connecting to Telegram Servers...</i>"
    )

    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")

    session = StringSession()
    client = TelegramClient(session, api_id, api_hash)
    
    try:
        await client.connect()
        sent = await client.send_code_request(phone)
        
        # Save session immediately to maintain context
        await state.update_data(
            session=session.save(), # Critical for session continuity
            phone=phone,
            phone_code_hash=sent.phone_code_hash,
            price=price,
            country_name=country_name,
            password_needed=False # Default false
        )
        
        await client.disconnect()
        
        await status_msg.edit_text(
            f"🌍 <b>Country:</b> {country_name}\n"
            f"💰 <b>Offer Price:</b> ₹{price}\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "📩 <b>OTP Sent!</b>\n\n"
            "Please check your Telegram Service notifications or SMS and enter the code below:\n"
            "<i>(Format: 12345)</i>"
        )
        await state.set_state(SellSession.waiting_sell_otp)

    except Exception as e:
        await client.disconnect()
        await status_msg.edit_text(f"❌ <b>Connection Failed:</b>\n<code>{str(e)}</code>")


# --- 3. User Sends OTP ---
@dp.message(StateFilter(SellSession.waiting_sell_otp))
async def user_sells_otp(msg: Message, state: FSMContext):
    otp_code = msg.text.strip()
    
    # Basic validation
    if not otp_code.isdigit():
        return await msg.answer("❌ <b>Invalid OTP.</b> Send numbers only.")

    data = await state.get_data()
    phone = data["phone"]
    session_str = data["session"]
    phone_code_hash = data["phone_code_hash"]

    status_msg = await msg.answer("🔄 <i>Verifying Code...</i>")

    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")
    client = TelegramClient(StringSession(session_str), api_id, api_hash)

    try:
        await client.connect()
        
        try:
            # Try logging in
            await client.sign_in(phone=phone, code=otp_code, phone_code_hash=phone_code_hash)
            
            # --- SCENARIO A: Login Successful (No 2FA) ---
            final_string = client.session.save() # CAPTURE FINAL STRING
            await client.disconnect()
            
            await state.update_data(string_session=final_string, password=None)
            
            # Skip password step, go directly to finalize logic
            await finalize_sell(msg, state, phone, final_string, None)
            
        except SessionPasswordNeededError:
            # --- SCENARIO B: 2FA Required ---
            await client.disconnect()
            await state.update_data(password_needed=True)
            await status_msg.delete()
            await msg.answer(
                "🔐 <b>Two-Step Verification Detected</b>\n\n"
                "Please enter your <b>Password</b> to complete the login.\n"
                "<i>We need this to verify the account.</i>"
            )
            await state.set_state(SellSession.waiting_sell_password)

    except PhoneCodeInvalidError:
        await client.disconnect()
        await status_msg.edit_text("❌ <b>Wrong OTP!</b>\nPlease check and send again.")
    except Exception as e:
        await client.disconnect()
        await status_msg.edit_text(f"❌ <b>Error:</b> {e}")


# --- 4. User Sends Password (If 2FA) ---
@dp.message(StateFilter(SellSession.waiting_sell_password))
async def user_sell_password(msg: Message, state: FSMContext):
    password = msg.text.strip()
    data = await state.get_data()
    
    phone = data["phone"]
    session_str = data["session"] # Use the initial session to resume
    
    status_msg = await msg.answer("🔄 <i>Verifying Password...</i>")

    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")
    client = TelegramClient(StringSession(session_str), api_id, api_hash)

    try:
        await client.connect()
        await client.sign_in(password=password)
        
        # --- Login Successful (With 2FA) ---
        final_string = client.session.save() # CAPTURE FINAL STRING
        await client.disconnect()
        
        # Proceed to finalize
        await status_msg.delete()
        await finalize_sell(msg, state, phone, final_string, password)

    except PasswordHashInvalidError:
        await client.disconnect()
        await status_msg.edit_text("❌ <b>Wrong Password!</b>\nPlease try again.")
    except Exception as e:
        await client.disconnect()
        await status_msg.edit_text(f"❌ <b>Error:</b> {e}")


# --- 5. Finalize Sell (Save to DB & Notify Admin) ---
async def finalize_sell(msg: Message, state: FSMContext, phone, string_session, password):
    data = await state.get_data()
    country_name = data["country_name"]
    price = data["price"]
    user_id = msg.from_user.id
    username = msg.from_user.username

    # 1. Update Database
    numbers_col.update_one(
        {"number": phone},
        {
            "$set": {
                "country": country_name,
                "number": phone,
                "string_session": string_session, # The valid authenticated session
                "password": password if password else "None",
                "used": False,
                "added_by": user_id,
                "added_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )

    # 2. Notify Admin
    # Using the specific Admin ID provided in your prompt
    ADMIN_CHAT_ID = -1003208353049 

    kb = InlineKeyboardBuilder()
    # Unique callback for selling OTPs
    kb.button(text="📩 Get OTP (Sell)", callback_data=f"get_sell_otp:{phone}")
    kb.button(text=f"✅ Approve ₹{price}", callback_data=f"approve_sell:{user_id}:{phone}:{price}")
    kb.button(text=f"Reject", callback_data=f"reject_sell:{user_id}:{phone}")
    
    kb.adjust(1)

    admin_text = (
        f"<b>📤 NEW ACCOUNT FOR SALE</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Seller:</b> @{username or 'N/A'} (<code>{user_id}</code>)\n"
        f"🌍 <b>Country:</b> {country_name}\n"
        f"📞 <b>Number:</b> <code>{phone}</code>\n"
        f"💰 <b>Payout:</b> ₹{price}\n"
        f"🔐 <b>2FA Pass:</b> <code>{password if password else 'None'}</code>\n\n"
        f"🔑 <b>Session String:</b>\n"
        f"<blockquote expandable><code>{string_session}</code></blockquote>"
    )

    try:
        await bot.send_message(
            ADMIN_CHAT_ID,
            admin_text,
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Failed to send to admin: {e}")

    # 3. Notify User
    await msg.answer(
        f"✅ <b>Submission Successful!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📞 <b>Number:</b> {phone}\n"
        f"💰 <b>Pending:</b> ₹{price}\n\n"
        f"<i>Your account is under review. Balance will be credited after admin verification (usually 1-10 mins).</i>"
    )
    
    await state.clear()

# ==========================================
# 📩 DEDICATED SELL OTP LISTENER (FIXED)
# ==========================================

@dp.callback_query(F.data.startswith("get_sell_otp:"))
async def callback_get_sell_otp(cq: CallbackQuery):
    phone = cq.data.split(":")[1]
    
    # 1. Fetch Session from DB
    number_doc = numbers_col.find_one({"number": phone})
    if not number_doc or not number_doc.get("string_session"):
        return await cq.answer("❌ Session not found in Database.", show_alert=True)

    await cq.answer("🔄 Accessing Account...", show_alert=False)
    
    # High UI status message
    status_msg = await cq.message.answer(f"🔍 <b>Searching for OTP on {phone}...</b>")

    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")
    string_session = number_doc.get("string_session")
    password_text = number_doc.get("password") or "None"

    client = TelegramClient(StringSession(string_session), api_id, api_hash)
    
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            await client.disconnect()
            await status_msg.edit_text(f"❌ <b>Session Expired</b>\nAccount {phone} has been logged out.")
            return

        # Use the logic from your working otp_listener
        # Matches any 5-digit number in the message
        pattern = re.compile(r"\b\d{5}\b")
        found_code = None

        # Iterate messages from Telegram Service (777000)
        # Increased limit slightly to ensure we don't miss it
        async for msg in client.iter_messages(777000, limit=15):
            if not msg.message:
                continue

            match = pattern.search(msg.message)
            if match:
                found_code = match.group(0)
                # We stop at the very first (newest) 5-digit code found
                break 
        
        await client.disconnect()

        if found_code:
            # High UI Result Format
            response_text = (
                f"<b>✅ OTP RECEIVED</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"<b>Code -</b> <code>{found_code}</code>\n"
                f"<b>Number -</b> <code>{phone}</code>\n"
                f"<b>Pass -</b> <code>{password_text}</code>\n"
                f"━━━━━━━━━━━━━━━━━━━━━"
            )
            
            await status_msg.delete()
            await bot.send_message(
                chat_id=cq.message.chat.id,
                text=response_text,
                parse_mode="HTML"
            )
        else:
            await status_msg.edit_text(
                f"⚠️ <b>OTP Not Found</b>\n"
                f"No 5-digit code found in the last 15 messages from Telegram on {phone}.\n\n"
                f"<i>Try clicking the button again in a few seconds.</i>"
            )

    except Exception as e:
        if client.is_connected():
            await client.disconnect()
        await status_msg.edit_text(f"❌ <b>Error:</b>\n<code>{str(e)}</code>")
        





# --- Admin: Get OTP Button ---

@dp.callback_query(F.data.startswith("get_otp:"))
async def callback_get_otp(cq: CallbackQuery):
    phone = cq.data.split(":")[1]

    number_doc = numbers_col.find_one({"number": phone})
    if not number_doc:
        return await cq.answer("❌ Number session not found.", show_alert=True)

    await cq.answer("Waiting for OTP.....")

    # 👇 pass message_id of SAME message
    asyncio.create_task(
        otp_listener(
            number_doc=number_doc,
            user_id=cq.from_user.id,
            message_id=cq.message.message_id
        )
    )


        
    
# --- 2. Admin: Approve Sell ---
@dp.callback_query(F.data.startswith("approve_sell:"))
async def callback_approve_sell(cq: CallbackQuery):
    if not is_admin(cq.from_user.id):
        return await cq.answer("❌ Not authorized.", show_alert=True)

    _, user_id, phone, price = cq.data.split(":")
    user_id, price = int(user_id), int(price)

    # Add Balance
    users_col.update_one({"_id": user_id}, {"$inc": {"balance": price}})

    # Edit Admin Message
    await cq.message.edit_text(
        cq.message.text + f"\n\n✅ <b>Approved by {cq.from_user.first_name}</b>",
        parse_mode="HTML"
    )

    # Notify User with Withdraw Button
    kb = InlineKeyboardBuilder()
    kb.button(text="💸 Withdraw Now", callback_data="init_withdraw")
    
    await bot.send_message(
        user_id,
        f"🎉 <b>Account Approved!</b>\n\n"
        f"✅ Account: <code>{phone}</code>\n"
        f"💰 Added: ₹{price}\n\n"
        f"You can withdraw this amount to your UPI immediately.",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )
    await cq.answer("✅ Approved & Balance Added.")

# --- 3. Admin: Reject Sell ---
@dp.callback_query(F.data.startswith("reject_sell:"))
async def callback_reject_sell(cq: CallbackQuery):
    if not is_admin(cq.from_user.id):
        return await cq.answer("❌ Not authorized.")

    _, user_id, phone = cq.data.split(":")
    user_id = int(user_id)

    await cq.message.edit_text(
        cq.message.text + f"\n\n❌ <b>Rejected by {cq.from_user.first_name}</b>",
        parse_mode="HTML"
    )
    
    await bot.send_message(
        user_id,
        f"⚠️ <b>Account Rejected</b>\n\nYour submission for <code>{phone}</code> was declined by the admin.",
        parse_mode="HTML"
    )
    await cq.answer("❌ Request Rejected.")
    


# --- Add Sell Button in Main Menu ---
# Add this line inside your main menu keyboard in cmd_start():
# kb.row(InlineKeyboardButton(text="💸 Sell Account", callback_data="sell"))



# --- 1. Init Withdrawal ---
@dp.callback_query(F.data == "init_withdraw")
async def start_withdraw(cq: CallbackQuery, state: FSMContext):
    user_bal = get_user_balance(cq.from_user.id)
    if user_bal < 1:
        return await cq.answer("❌ Balance too low.", show_alert=True)

    kb = InlineKeyboardBuilder()
    kb.button(text="🇮🇳 INR (UPI)", callback_data="wd_inr")
    kb.button(text="🪙 USDT (Crypto)", callback_data="wd_usdt")
    kb.adjust(2)

    await cq.message.answer(
        "🏦 <b>Withdrawal Setup</b>\n\nChoose your preferred withdrawal currency:",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )
    await cq.answer()

# --- 2. Handle Currency Choice ---
@dp.callback_query(F.data.in_(["wd_inr", "wd_usdt"]))
async def choose_currency(cq: CallbackQuery, state: FSMContext):
    if cq.data == "wd_inr":
        await cq.message.edit_text(
            "🏦 <b>INR Withdrawal</b>\n\nPlease enter your <b>UPI ID</b> (e.g., user@oksbi):",
            parse_mode="HTML"
        )
        await state.set_state(WithdrawState.waiting_inr_upi)
    
    elif cq.data == "wd_usdt":
        kb = InlineKeyboardBuilder()
        kb.button(text="Cwallet", callback_data="method_cwallet")
        kb.button(text="Binance", callback_data="method_binance")
        kb.button(text="BEP20", callback_data="method_bep20")
        kb.adjust(1)

        await cq.message.edit_text(
            "🪙 <b>USDT Withdrawal</b>\n\nChoose your withdrawal method:",
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )
        await state.set_state(WithdrawState.waiting_usdt_method)
    await cq.answer()

# ==========================================
#               INR FLOW
# ==========================================

@dp.message(StateFilter(WithdrawState.waiting_inr_upi))
async def process_inr_upi(msg: Message, state: FSMContext):
    upi_id = msg.text.strip()
    await state.update_data(address=upi_id, currency="INR", method="UPI")
    
    user_bal = get_user_balance(msg.from_user.id)
    
    await msg.answer(
        f"✅ UPI set to: <code>{upi_id}</code>\n\n"
        f"💰 Your Balance: ₹{user_bal}\n"
        f"Enter the amount in ₹ you want to withdraw (Min ₹1):",
        parse_mode="HTML"
    )
    await state.set_state(WithdrawState.waiting_inr_amount)

@dp.message(StateFilter(WithdrawState.waiting_inr_amount))
async def process_inr_amount(msg: Message, state: FSMContext):
    try:
        amount = int(msg.text.strip())
    except ValueError:
        return await msg.answer("❌ Please enter a valid number.")

    user_id = msg.from_user.id
    current_bal = get_user_balance(user_id)

    if amount > current_bal:
        return await msg.answer(f"❌ Insufficient funds. Your balance is ₹{current_bal}.")
    if amount < 1:
        return await msg.answer("❌ Minimum withdrawal is ₹1.")

    data = await state.get_data()
    upi_id = data.get('address')

    # Deduct & Save
    users_col.update_one({"_id": user_id}, {"$inc": {"balance": -amount}})
    
    withdraw_doc = {
        "user_id": user_id,
        "username": msg.from_user.username,
        "amount_inr": amount,
        "currency": "INR",
        "method": "UPI",
        "address": upi_id,
        "status": "pending"
    }
    result = withdrawals_col.insert_one(withdraw_doc)
    
    await msg.answer(
        f"✅ <b>Withdrawal Request Submitted!</b>\n"
        f"💸 Amount: ₹{amount}\n"
        f"🏦 UPI: <code>{upi_id}</code>\n\n"
        f"You will receive the funds shortly.",
        parse_mode="HTML"
    )
    await state.clear()
    await notify_admin(bot, withdraw_doc, str(result.inserted_id), msg.from_user.full_name)

# ==========================================
#               USDT FLOW
# ==========================================

@dp.callback_query(StateFilter(WithdrawState.waiting_usdt_method), F.data.startswith("method_"))
async def process_usdt_method(cq: CallbackQuery, state: FSMContext):
    method = cq.data.split("_")[1].capitalize() # Cwallet, Binance, or Bep20
    await state.update_data(method=method, currency="USDT")
    
    prompt = f"Please enter your <b>{method} ID / Address</b>:"
    await cq.message.edit_text(f"🪙 <b>{method} Selected</b>\n\n{prompt}", parse_mode="HTML")
    await state.set_state(WithdrawState.waiting_usdt_address)
    await cq.answer()

@dp.message(StateFilter(WithdrawState.waiting_usdt_address))
async def process_usdt_address(msg: Message, state: FSMContext):
    address = msg.text.strip()
    await state.update_data(address=address)
    
    user_bal = get_user_balance(msg.from_user.id)
    rate = await get_usdt_inr_rate()
    
    await msg.answer(
        f"✅ Address saved: <code>{address}</code>\n\n"
        f"💰 Your Balance: ₹{user_bal}\n"
        f"💱 Current USDT Rate: ₹{rate:.2f}\n\n"
        f"Enter the amount in <b>₹ (INR)</b> you want to withdraw:\n"
        f"<i>(It will be converted to USDT. Min withdrawal is $0.50)</i>",
        parse_mode="HTML"
    )
    await state.set_state(WithdrawState.waiting_usdt_amount)

@dp.message(StateFilter(WithdrawState.waiting_usdt_amount))
async def process_usdt_amount(msg: Message, state: FSMContext):
    try:
        amount_inr = int(msg.text.strip())
    except ValueError:
        return await msg.answer("❌ Please enter a valid number.")

    user_id = msg.from_user.id
    current_bal = get_user_balance(user_id)

    if amount_inr > current_bal:
        return await msg.answer(f"❌ Insufficient funds. Your balance is ₹{current_bal}.")

    # Convert to USDT & Check Min 0.5
    rate = await get_usdt_inr_rate()
    usdt_amount = round(amount_inr / rate, 2)

    if usdt_amount < 0.5:
        return await msg.answer(f"❌ Minimum withdrawal is $0.5 USDT. (₹{amount_inr} is approx ${usdt_amount})")

    data = await state.get_data()
    method = data.get('method')
    address = data.get('address')

    # Deduct & Save
    users_col.update_one({"_id": user_id}, {"$inc": {"balance": -amount_inr}})
    
    withdraw_doc = {
        "user_id": user_id,
        "username": msg.from_user.username,
        "amount_inr": amount_inr,
        "amount_usdt": usdt_amount,
        "currency": "USDT",
        "method": method,
        "address": address,
        "status": "pending"
    }
    result = withdrawals_col.insert_one(withdraw_doc)
    
    await msg.answer(
        f"✅ <b>Withdrawal Request Submitted!</b>\n"
        f"💸 Deducted: ₹{amount_inr}\n"
        f"🪙 Receiving: <b>${usdt_amount} USDT</b>\n"
        f"🏦 Method: {method}\n"
        f"📍 Address: <code>{address}</code>\n\n"
        f"You will receive the funds shortly.",
        parse_mode="HTML"
    )
    await state.clear()
    await notify_admin(bot, withdraw_doc, str(result.inserted_id), msg.from_user.full_name)

# ==========================================
#          ADMIN NOTIFICATION & PAY
# ==========================================

async def notify_admin(bot_instance, doc, req_id, full_name):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Approve Payment", callback_data=f"pay_wd:{req_id}")
    kb.adjust(1)

    if doc['currency'] == "INR":
        amount_text = f"💰 Amount: <b>₹{doc['amount_inr']}</b>"
    else:
        amount_text = f"💰 Amount: <b>${doc['amount_usdt']} USDT</b> (deducted ₹{doc['amount_inr']})"

    admin_text = (
        f"<b>💸 New Withdrawal Request</b>\n\n"
        f"👤 User: {full_name} (<code>{doc['user_id']}</code>)\n"
        f"{amount_text}\n"
        f"🏦 Method: {doc['method']}\n"
        f"📍 Address/UPI: <code>{doc['address']}</code>\n"
        f"🆔 Req ID: <code>{req_id}</code>"
    )

    await bot_instance.send_message(
        "-1003208353049", # Replace with actual admin chat ID
        admin_text,
        reply_markup=kb.as_markup(), 
        parse_mode="HTML"
    )

# --- Admin clicks Approve Payment ---
@dp.callback_query(F.data.startswith("pay_wd:"))
async def admin_approve_withdraw(cq: CallbackQuery, state: FSMContext):
    req_id = cq.data.split(":")[1]
    
    await state.update_data(req_id=req_id, message_id=cq.message.message_id, chat_id=cq.message.chat.id)
    
    await cq.message.answer(
        "✍️ <b>Send the Transaction ID (UTR/Hash) for this payment:</b>\n"
        "Or type /skip if you don't want to provide one.",
        parse_mode="HTML"
    )
    await state.set_state(AdminTxnState.waiting_txn)
    await cq.answer()

# --- Admin sends TXN ID ---
@dp.message(StateFilter(AdminTxnState.waiting_txn))
async def admin_finalize_withdraw(msg: Message, state: FSMContext):
    txn_id = msg.text.strip()
    data = await state.get_data()
    req_id = data.get('req_id')
    admin_msg_id = data.get('message_id')
    admin_chat_id = data.get('chat_id')

    req_doc = withdrawals_col.find_one({"_id": ObjectId(req_id)})
    if not req_doc:
        await msg.answer("❌ Error: Request not found in DB.")
        return await state.clear()

    # Update DB Status
    withdrawals_col.update_one({"_id": ObjectId(req_id)}, {"$set": {"status": "paid", "txn": txn_id}})

    # 1. Notify User
    if req_doc['currency'] == "INR":
        amount_str = f"₹{req_doc['amount_inr']}"
    else:
        amount_str = f"${req_doc['amount_usdt']} USDT"

    user_msg = (
        f"🎉 <b>Withdrawal Approved!</b>\n\n"
        f"💰 Amount: {amount_str}\n"
        f"🏦 Method: {req_doc['method']}\n"
        f"📍 Address: <code>{req_doc['address']}</code>\n"
    )
    if txn_id != "/skip":
        user_msg += f"🆔 TXN ID / Hash: <code>{txn_id}</code>"
    
    try:
        await bot.send_message(req_doc['user_id'], user_msg, parse_mode="HTML")
    except:
        pass # User might have blocked the bot

    # 2. Update Admin Group Message
    if req_doc['currency'] == "INR":
        amount_text = f"💰 Amount: <b>₹{req_doc['amount_inr']}</b>"
    else:
        amount_text = f"💰 Amount: <b>${req_doc['amount_usdt']} USDT</b> (deducted ₹{req_doc['amount_inr']})"

    original_text = (
        f"<b>💸 New Withdrawal Request</b>\n\n"
        f"👤 User: {req_doc['username']} (<code>{req_doc['user_id']}</code>)\n"
        f"{amount_text}\n"
        f"🏦 Method: {req_doc['method']}\n"
        f"📍 Address/UPI: <code>{req_doc['address']}</code>\n"
        f"🆔 Req ID: <code>{req_id}</code>"
    )

    strikethrough_text = f"<s>{original_text}</s>\n\n✅ <b>PAID by {msg.from_user.first_name}</b>"
    if txn_id != "/skip":
        strikethrough_text += f"\n🆔 Ref: {txn_id}"

    try:
        await bot.edit_message_text(
            chat_id=admin_chat_id,
            message_id=admin_msg_id,
            text=strikethrough_text,
            parse_mode="HTML"
        )
    except Exception as e:
        await msg.answer(f"⚠️ Could not edit original message: {e}")

    await msg.answer("✅ Withdrawal marked as paid.")
    await state.clear()


# ================= /editcountry Flow =================

@dp.message(Command("editcountry"))
async def cmd_edit_country(msg: Message):
    if not is_admin(msg.from_user.id): 
        return
    
    # Using list() instead of async for to prevent the PyMongo Cursor error
    countries = list(countries_col.find({}))
    if not countries:
        return await msg.answer("❌ No countries found.")
        
    kb = InlineKeyboardBuilder()
    for c in countries:
        kb.button(text=c["name"], callback_data=f"edit_c:{c['name']}")
    kb.adjust(2)
    
    await msg.answer("🌍 <b>Select a country to edit:</b>", reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "back_to_country_list")
async def cb_back_to_country_list(cq: CallbackQuery, state: FSMContext):
    await state.clear()
    countries = list(countries_col.find({}))
    if not countries:
        return await cq.message.edit_text("❌ No countries found.")
        
    kb = InlineKeyboardBuilder()
    for c in countries:
        kb.button(text=c["name"], callback_data=f"edit_c:{c['name']}")
    kb.adjust(2)
    
    await cq.message.edit_text("🌍 <b>Select a country to edit:</b>", reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("edit_c:"))
async def cb_edit_country_selected(cq: CallbackQuery, state: FSMContext):
    country_name = cq.data.split(":")[1]
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Change Name", callback_data=f"edit_c_name:{country_name}"),
            InlineKeyboardButton(text="💰 Change Price", callback_data=f"edit_c_price:{country_name}")
        ],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_country_list")]
    ])
    
    await cq.message.edit_text(
        f"🛠 <b>Editing Country:</b> <code>{country_name}</code>\n\n"
        f"What would you like to change?",
        parse_mode="HTML",
        reply_markup=kb
    )

# --- Change Name Flow ---
@dp.callback_query(F.data.startswith("edit_c_name:"))
async def cb_edit_country_name(cq: CallbackQuery, state: FSMContext):
    country_name = cq.data.split(":")[1]
    await state.update_data(editing_country=country_name)
    await state.set_state(EditCountryFSM.waiting_new_name)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Cancel", callback_data="back_to_country_list")]
    ])
    await cq.message.edit_text(
        f"✏️ Enter the <b>NEW NAME</b> for <code>{country_name}</code>:", 
        parse_mode="HTML", 
        reply_markup=kb
    )

@dp.message(StateFilter(EditCountryFSM.waiting_new_name))
async def process_new_country_name(msg: Message, state: FSMContext):
    data = await state.get_data()
    old_name = data.get("editing_country")
    new_name = msg.text.strip()
    
    # Update the country name
    countries_col.update_one({"name": old_name}, {"$set": {"name": new_name}})
    
    # CRITICAL: Also update associated numbers and orders so they don't become orphaned!
    numbers_col.update_many({"country": old_name}, {"$set": {"country": new_name}})
    orders_col.update_many({"country": old_name}, {"$set": {"country": new_name}})
    
    await msg.answer(f"✅ Country name changed from <b>{old_name}</b> to <b>{new_name}</b>.", parse_mode="HTML")
    await state.clear()

# --- Change Price Flow ---
@dp.callback_query(F.data.startswith("edit_c_price:"))
async def cb_edit_country_price(cq: CallbackQuery, state: FSMContext):
    country_name = cq.data.split(":")[1]
    await state.update_data(editing_country=country_name)
    await state.set_state(EditCountryFSM.waiting_new_price)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Cancel", callback_data="back_to_country_list")]
    ])
    await cq.message.edit_text(
        f"💰 Enter the <b>NEW PRICE</b> for <code>{country_name}</code>:", 
        parse_mode="HTML", 
        reply_markup=kb
    )

@dp.message(StateFilter(EditCountryFSM.waiting_new_price))
async def process_new_country_price(msg: Message, state: FSMContext):
    data = await state.get_data()
    country_name = data.get("editing_country")
    
    try:
        new_price = float(msg.text.strip())
    except ValueError:
        return await msg.answer("❌ Invalid price format. Please enter a valid number.")
        
    countries_col.update_one({"name": country_name}, {"$set": {"price": new_price}})
    
    await msg.answer(f"✅ Price for <b>{country_name}</b> updated to <b>{fmt_curr(new_price)}</b>.", parse_mode="HTML")
    await state.clear()

@dp.callback_query(F.data == "stats")
async def callback_howto(cq: CallbackQuery):

    # --- Get or create user ---
    user = users_col.find_one({"_id": cq.from_user.id})
    if not user:
        user = get_or_create_user(
            cq.from_user.id,
            cq.from_user.username
        )

    # --- SAFE USER DATA (IMPORTANT) ---
    full_name = escape(cq.from_user.full_name or "User")
    username = (
        f"@{escape(cq.from_user.username)}"
        if cq.from_user.username else "N/A"
    )

    user_id = cq.from_user.id
    balance = float(user.get("balance", 0.0))

    safe_bot = escape(BOTUSER)
    safe_sales = escape(SALESLOG)

    # --- TEXT ---
    steps_text = (
        f'<b>◍ Tgbitz Bot - Accounts & SMM</b>\n'
        f'––––––——–––————––––——–––•\n'
        f'<blockquote><b><tg-emoji emoji-id="5409132617750555920">💳</tg-emoji> Name:</b> {full_name}</blockquote>\n'
        f'<blockquote><b><tg-emoji emoji-id="5408910121264756249">❌</tg-emoji> Username:</b> {username}</blockquote>\n'
        f'<blockquote><b><tg-emoji emoji-id="5409230963911701228">❌</tg-emoji> User ID:</b> <code>{user_id}</code></blockquote>\n'
        f'<blockquote><b><tg-emoji emoji-id="5409078930659357770">❌</tg-emoji> Balance:</b> {fmt_curr(balance)}</blockquote>\n'
        f'––––––——–––————––––——–––•\n'
        f'• <b>Bot:</b> @{safe_bot}'
    )

    # --- KEYBOARD ---
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(
            text="▪️ Support",
            url=f"https://t.me/{OWNER}",
            style="success"
        ),
        InlineKeyboardButton(
            text="▪️ 𝙃𝙤𝙬 𝙩𝙤 𝙪𝙨𝙚",
            url="https://t.me/tgbitz_guidence/3",
            style="success"
        )
    )

    kb.row(
        InlineKeyboardButton(text="📑 History", callback_data="history", style="danger")
    )

    kb.row(
        InlineKeyboardButton(text="▪️ Previous", callback_data="back_main", style="danger")
    )

    # --- SEND ---
    await cq.message.edit_text(
        steps_text,
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )

    await cq.answer()

@dp.callback_query(F.data == "howto")
async def callback_howto(cq: CallbackQuery):
    await cq.answer() # Answer first
    steps_text = ("📚 FᴀQ & Sᴜᴘᴘᴏʀᴛ 😊\n\n🔗 𝙃𝙤𝙬 𝙩𝙤 𝙪𝙨𝙚:👉 {USAGE}\n💬 Oғғɪᴄɪᴀʟ Sᴜᴘᴘᴏʀᴛ:   👉 {SUPPORT}\n🤖 Oғғɪᴄɪᴀʟ Bᴏᴛ:     👉 {BOT_USER}\n\n🛟 Fᴇᴇʟ Fʀᴇᴇ Tᴏ Rᴇᴀᴄʜ Oᴜ𝙩 Iғ Yᴏᴜ Nᴇᴇᴅ Aɴʏ Hᴇʟᴘ!")
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="📲 Support", url=f"https://t.me/{SUPPORT}", style="success"),
        InlineKeyboardButton(text="🔗 𝙃𝙤𝙬 𝙩𝙤 𝙪𝙨𝙚", url=f"https://t.me/tgbitz_guidence/3", style="success")
    )
    # Added back button
    kb.row(InlineKeyboardButton(text="🔙 Main Menu", callback_data="main_menu", style="danger")) 
    
    await cq.message.edit_text(steps_text, parse_mode="HTML", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "refer")
async def callback_refer(cq: CallbackQuery):
    # Generate Link
    bot_username = (await bot.get_me()).username
    refer_link = f"https://t.me/{bot_username}?start=ref{cq.from_user.id}"

    text = (
        "🤝 <b>Refer & Earn Program</b>\n\n"
        "Invite your friends and earn passive balance\n"
        "You will receive <b>3% commission</b> on <i>every</i> deposit they make.\n\n"
        f"🔗 <b>Your Link:</b>\n<code>{refer_link}</code>"
    )

    kb = InlineKeyboardBuilder()
    kb.button(text="📤 Share Link", url=f"https://t.me/share/url?url={refer_link}&text=Join%20this%20bot%20to%20buy%20cheap%20accounts!", style="success")
    kb.adjust(1)
    kb.button(text="🔙 Back", callback_data="back_main", style="danger")

    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    
# ================= Bulk 2FA Changer =================

@dp.message(Command("2fa"))
async def cmd_bulk_2fa(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ Not authorized.")
        
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="admin_back")]])
    await msg.answer(
        "🗜️ <b>Bulk 2FA Changer</b>\n\n"
        "Please send a <code>.zip</code> file containing your `.session` files:",
        parse_mode="HTML", reply_markup=kb
    )
    await state.set_state(BulkChange2FAFSM.waiting_for_zip)

@dp.message(StateFilter(BulkChange2FAFSM.waiting_for_zip), F.document)
async def bulk_2fa_receive_zip(msg: Message, state: FSMContext):
    if not msg.document.file_name.endswith('.zip'):
        return await msg.answer("❌ Please send a valid `.zip` archive.")
        
    status_msg = await msg.answer("⏳ <i>Extracting sessions...</i>", parse_mode="HTML")
    
    workspace = f"temp_2fa/{msg.from_user.id}_{int(time.time())}"
    extract_dir = f"{workspace}/extracted"
    os.makedirs(extract_dir, exist_ok=True)
    
    zip_path = f"{workspace}/input.zip"
    await bot.download(msg.document, destination=zip_path)
    
    try:
        shutil.unpack_archive(zip_path, extract_dir)
    except Exception as e:
        shutil.rmtree(workspace, ignore_errors=True)
        return await status_msg.edit_text("❌ Failed to extract the zip file.")
        
    session_files = glob.glob(f"{extract_dir}/**/*.session", recursive=True)
    
    if not session_files:
        shutil.rmtree(workspace, ignore_errors=True)
        return await status_msg.edit_text("❌ No `.session` files found in the zip.")
        
    await state.update_data(session_files=session_files, workspace=workspace)
    
    await status_msg.edit_text(
        f"✅ <b>Found {len(session_files)} sessions.</b>\n\n"
        f"⌨️ <b>Enter the CURRENT 2FA password:</b>\n"
        f"<i>(Type <code>None</code> if they don't have one)</i>", 
        parse_mode="HTML"
    )
    await state.set_state(BulkChange2FAFSM.waiting_for_current_pass)

@dp.message(StateFilter(BulkChange2FAFSM.waiting_for_current_pass))
async def bulk_2fa_current_pass(msg: Message, state: FSMContext):
    curr_pass = msg.text.strip()
    if curr_pass.lower() == "none":
        curr_pass = None
        
    await state.update_data(current_pass=curr_pass)
    
    await msg.answer(
        "⌨️ <b>Enter the NEW 2FA password:</b>\n"
        "<i>(Type <code>None</code> to remove 2FA completely)</i>", 
        parse_mode="HTML"
    )
    await state.set_state(BulkChange2FAFSM.waiting_for_new_pass)

@dp.message(StateFilter(BulkChange2FAFSM.waiting_for_new_pass))
async def bulk_2fa_execute(msg: Message, state: FSMContext):
    new_pass = msg.text.strip()
    if new_pass.lower() == "none":
        new_pass = None
        
    data = await state.get_data()
    curr_pass = data["current_pass"]
    session_files = data["session_files"]
    workspace = data["workspace"]
    
    status_msg = await msg.answer(
        f"🔄 <i>Processing {len(session_files)} sessions... Changing 2FA...</i>", 
        parse_mode="HTML"
    )
    
    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")
    
    success_count = 0
    failed_count = 0
    
    # Process each session file
    for path in session_files:
        try:
            # Silently force the schema fix so it doesn't crash on Pyrogram files
            fix_telethon_session(path)
        except Exception:
            pass

        client = TelegramClient(path.replace(".session", ""), api_id, api_hash)
        try:
            await client.connect()
            if await client.is_user_authorized():
                await client.edit_2fa(current_password=curr_pass, new_password=new_pass)
                success_count += 1
            else:
                failed_count += 1
        except Exception as e:
            print(f"Failed to change 2FA for {path}: {e}")
            failed_count += 1
        finally:
            if client.is_connected():
                await client.disconnect()
                
    await status_msg.edit_text("🗜️ <i>Re-packing updated sessions into a ZIP...</i>", parse_mode="HTML")
    
    output_zip_name = f"Updated_2FA_{int(time.time())}.zip"
    output_zip_path = f"{workspace}/{output_zip_name}"
    
    try:
        # Create final ZIP with modified sessions
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in session_files:
                zf.write(file_path, os.path.basename(file_path)) # Writes flat, removing folders
        
        doc = FSInputFile(output_zip_path)
        await msg.answer_document(
            document=doc,
            caption=(
                f"✅ <b>Bulk 2FA Update Complete!</b>\n\n"
                f"🟢 <b>Success:</b> {success_count}\n"
                f"🔴 <b>Failed/Dead:</b> {failed_count}\n\n"
                f"🔑 <b>New Password:</b> <code>{new_pass if new_pass else 'Removed'}</code>"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        await msg.answer(f"❌ Failed to create final ZIP: <code>{e}</code>", parse_mode="HTML")
    finally:
        # Erase everything from server once done
        shutil.rmtree(workspace, ignore_errors=True)
        await status_msg.delete()
        await state.clear()

# ================= Admin SMM Management =================
@dp.message(Command("smm"))
async def cmd_admin_smm(msg: Message):
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ Not authorized.")

    healthy_count = numbers_col.count_documents({"status": "healthy", "used": False})
    
    text = (
        f"⚙️ <b>SMM Control Panel</b>\n"
        f"––––––––––––––————––•\n"
        f"Total Available Sessions (Healthy): <b>{healthy_count}</b>\n\n"
        f"Select an action below:"
    )
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="💰 Set Prices", callback_data="admin_smm_prices"))
    kb.row(InlineKeyboardButton(text="📢 Broadcast to GC", callback_data="admin_smm_soon"))
    kb.row(InlineKeyboardButton(text="🚪 Leave all Groups", callback_data="admin_smm_soon"))
    kb.row(InlineKeyboardButton(text="❌ Close", callback_data="delete_msg"))
    
    await msg.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "admin_smm_prices")
async def admin_smm_prices_menu(cq: CallbackQuery):
    kb = InlineKeyboardBuilder()
    for s in default_services:
        kb.button(text=s.replace("_", " ").title(), callback_data=f"smm_setprice:{s}")
    kb.adjust(2)
    kb.row(InlineKeyboardButton(text="🔙 Back", callback_data="admin_smm_back"))
    
    await cq.message.edit_text("Select a service to set its price and min-buy:", reply_markup=kb.as_markup())
    await cq.answer()

@dp.callback_query(F.data.startswith("smm_setprice:"))
async def admin_smm_setprice_prompt(cq: CallbackQuery, state: FSMContext):
    service = cq.data.split(":")[1]
    await state.update_data(editing_service=service)
    await cq.message.edit_text(
        f"Send the price per action and minimum buy for <b>{service.upper()}</b>.\n\n"
        f"Format: <code>price,min_buy</code>\n"
        f"Example: <code>2.5,10</code>", parse_mode="HTML"
    )
    await state.set_state(SMMAdminFlow.waiting_for_price)
    await cq.answer()

@dp.message(StateFilter(SMMAdminFlow.waiting_for_price))
async def admin_smm_setprice_save(msg: Message, state: FSMContext):
    data = await state.get_data()
    service = data.get("editing_service")
    
    try:
        price_str, min_str = msg.text.split(",")
        price = float(price_str.strip())
        min_buy = int(min_str.strip())
        
        smm_col.update_one({"service": service}, {"$set": {"price": price, "min_buy": min_buy}})
        await msg.answer(f"✅ Updated <b>{service.upper()}</b>:\nPrice: {fmt_curr(price)}\nMin Buy: {min_buy}", parse_mode="HTML")
        await state.clear()
    except Exception:
        await msg.answer("❌ Invalid format. Use: <code>price,min_buy</code> (e.g. 2,10)", parse_mode="HTML")

@dp.callback_query(F.data == "admin_smm_soon")
async def admin_smm_soon(cq: CallbackQuery):
    await cq.answer("⏳ Feature coming soon in the next update!", show_alert=True)

@dp.callback_query(F.data == "admin_smm_back")
async def admin_smm_back(cq: CallbackQuery):
    await cmd_admin_smm(cq.message)
    await cq.answer()

# ================= FSM States =================


# ================= User SMM Menu =================
@dp.callback_query(F.data == "feature_smm")
async def callback_smm_menu_hub(cq: CallbackQuery, state: FSMContext):
    await state.clear()
    text = (
        f"<b>Welcome to  SMM 🥂</b>\n"
        f"––––––––––––––————––•\n"
        f"<blockquote>• Select what SMM service platform you want\n"
        f"• Telegram (In-App Accounts) or External APIs\n"
        f"• Quality guaranteed on all servers 🍷</blockquote>"
    )
    
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(
            text="Telegram (In app - Dm, votes etc)", 
            callback_data="feature_smm_inapp" # Changed callback
        )
    )
    kb.row(
        InlineKeyboardButton(
            text="SMM Panel (External - Insta, YT etc)", 
            callback_data="feature_smm_external" # Connects to smmpanel.py
        )
    )
    kb.row(InlineKeyboardButton(text="🔙 Back", callback_data="back_main", style="danger"))
    
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await cq.answer()

# Map the old feature_smm endpoint to the new specific name
@dp.callback_query(F.data == "feature_smm_inapp")
async def callback_smm_inapp_menu(cq: CallbackQuery, state: FSMContext):
    # Paste your ORIGINAL feature_smm content here. 
    await state.clear()
    text = (
        f"<b>Welcome to tgbitz SMM</b>\n"
        f"––––––––––––––————––•\n"
        f"• buy smm services for telegram\n"
        f"• votes, joins, mass dm, reactions etc\n"
        f"• No third-party panel, all services are of bot\n"
        f"- select what you wanna buy"
    )
    
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="👍 Votes/Polls", callback_data="smm_select:votes"),
        InlineKeyboardButton(text="🚪 Joins", callback_data="smm_select:joins")
    )
    kb.row(
        InlineKeyboardButton(text="❤️ Reactions", callback_data="smm_select:reactions"),
        InlineKeyboardButton(text="💬 Mass DM", callback_data="smm_select:mass_dm")
    )
    kb.row(
        InlineKeyboardButton(text="👁️ Views", callback_data="smm_select:views"),
    )
    kb.row(InlineKeyboardButton(text="🔙 Back", callback_data="back_main", style="danger"))
    
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await cq.answer()
    

# ================= Numpad UI Generator =================
async def render_smm_numpad(cq: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    service = data['service']
    qty_str = data.get("qty", "0")
    qty = int(qty_str) if qty_str else 0
    
    settings = smm_col.find_one({"service": service})
    price_per = settings.get("price", 2.0)
    min_buy = settings.get("min_buy", 5)
    
    healthy_count = numbers_col.count_documents({"status": "healthy", "used": False})
    total_price = qty * price_per

    text = (
        f"<b>How do you want buy-(SMM)</b>\n"
        f"––––––––––––––————––•\n"
        f"• <u>Service</u>  →  {service.replace('_', ' ').title()}\n"
        f"• <u>Condition</u> - Healthy\n"
        f"• <u>Key-code</u>   →  [SES-SMM]\n"
        f"• <u>Available</u>   →  {healthy_count} SESSION\n"
        f"• <u>Price</u>  →  {fmt_curr(price_per)}/each\n"
        f"• <u>Min Buy</u>  →  {min_buy}\n"
    )

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=f"SES: {qty} | Total: {fmt_curr(total_price)}", callback_data="ignore"))
    for row in (("1", "2", "3"), ("4", "5", "6"), ("7", "8", "9")):
        kb.row(*[InlineKeyboardButton(text=btn, callback_data=f"smm_num:{btn}") for btn in row])
    kb.row(
        InlineKeyboardButton(text="Buy ✅", callback_data="smm_buy_confirm"),
        InlineKeyboardButton(text="0", callback_data="smm_num:0"),
        InlineKeyboardButton(text="⌫", callback_data="smm_num:del")
    )
    kb.row(InlineKeyboardButton(text="Back", callback_data="feature_smm_inapp", icon_custom_emoji_id="5409284148491726576", style="danger"))

    try:
        await cq.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    except Exception:
        pass 

@dp.callback_query(F.data.startswith("smm_select:"))
async def smm_select_service(cq: CallbackQuery, state: FSMContext):
    service = cq.data.split(":")[1]
    await state.update_data(service=service, qty="0")
    await state.set_state(SMMBuyFlow.waiting_qty)
    await render_smm_numpad(cq, state)
    await cq.answer()

@dp.callback_query(StateFilter(SMMBuyFlow.waiting_qty), F.data.startswith("smm_num:"))
async def smm_numpad_input(cq: CallbackQuery, state: FSMContext):
    val = cq.data.split(":")[1]
    data = await state.get_data()
    current = data.get("qty", "0")
    
    if val == "del":
        current = current[:-1] if len(current) > 1 else "0"
    else:
        current = val if current == "0" else current + val
    
    await state.update_data(qty=current)
    await render_smm_numpad(cq, state)
    await cq.answer()

@dp.callback_query(StateFilter(SMMBuyFlow.waiting_qty), F.data == "smm_buy_confirm")
async def smm_buy_confirm(cq: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    qty = int(data.get("qty", "0"))
    service = data['service']
    
    settings = smm_col.find_one({"service": service})
    min_buy = settings.get("min_buy", 5)
    price_per = settings.get("price", 2.0)
    total_price = qty * price_per
    user_bal = get_user_balance(cq.from_user.id)
    available = numbers_col.count_documents({"status": "healthy", "used": False})
    
    if qty < min_buy:
        return await cq.answer(f"⚠️ Minimum buy is {min_buy}", show_alert=True)
    if qty > available:
        return await cq.answer(f"⚠️ Only {available} sessions available", show_alert=True)
    if user_bal < total_price:
        return await cq.answer("❌ Insufficient Balance! Please Recharge.", show_alert=True)

    await cq.message.edit_reply_markup(reply_markup=None) 
    
    if service == "joins":
        await cq.message.edit_text("🔗 Send the Channel/Group link.\n\n<i>Note: If you want to get requests, send the private request link.</i>", parse_mode="HTML")
        await state.set_state(SMMBuyFlow.waiting_channel_link)
        
    elif service in ["votes", "vote_poll"]:
        await cq.message.edit_text("🔗 First, send the Channel link where the post is located:", parse_mode="HTML")
        await state.set_state(SMMBuyFlow.waiting_channel_link)
        
    elif service == "views":
        await cq.message.edit_text("🔗 Send the direct public Post Link (e.g. t.me/channel/123):", parse_mode="HTML")
        await state.set_state(SMMBuyFlow.waiting_post_link)
        
    elif service == "reactions":
        kb = InlineKeyboardBuilder()
        kb.button(text="👍,♥️,🔥 Positive", callback_data="smm_react:happy")
        kb.button(text="👎,🖕,🤮 Negative", callback_data="smm_react:sad")
        kb.adjust(1,1)
        await cq.message.edit_text("❤️ Do you want Happy or Sad reactions?", reply_markup=kb.as_markup())
        await state.set_state(SMMBuyFlow.waiting_reaction_type)
        
    elif service == "mass_dm":
        await cq.message.edit_text("👤 Send the target Username (e.g. @username) you want to mass DM:", parse_mode="HTML")
        await state.set_state(SMMBuyFlow.waiting_dm_target)
        
    await cq.answer()

# --- Collect Inputs Handlers ---
@dp.callback_query(StateFilter(SMMBuyFlow.waiting_reaction_type), F.data.startswith("smm_react:"))
async def smm_react_type(cq: CallbackQuery, state: FSMContext):
    await state.update_data(reaction_type=cq.data.split(":")[1])
    await cq.message.edit_text("🔗 Now, send the Channel joining link:", parse_mode="HTML")
    await state.set_state(SMMBuyFlow.waiting_channel_link)
    await cq.answer()

@dp.message(StateFilter(SMMBuyFlow.waiting_dm_target))
async def smm_dm_target(msg: Message, state: FSMContext):
    await state.update_data(dm_target=msg.text.strip())
    kb = InlineKeyboardBuilder()
    kb.button(text="🎲 Random Bot Messages", callback_data="smm_dm_type:random")
    kb.button(text="✍️ Custom Message", callback_data="smm_dm_type:custom")
    kb.adjust(1,1)
    await msg.answer("Do you want random organic messages or a custom text?", reply_markup=kb.as_markup())
    await state.set_state(SMMBuyFlow.waiting_dm_type)

@dp.callback_query(StateFilter(SMMBuyFlow.waiting_dm_type), F.data.startswith("smm_dm_type:"))
async def smm_dm_type(cq: CallbackQuery, state: FSMContext):
    if cq.data.split(":")[1] == "custom":
        await cq.message.edit_text("✍️ Send your custom message (Max 2 lines):")
        await state.set_state(SMMBuyFlow.waiting_dm_custom_text)
    else:
        await state.update_data(dm_text="random")
        await start_smm_execution(cq.message, state, cq.from_user.id)
    await cq.answer()

@dp.message(StateFilter(SMMBuyFlow.waiting_dm_custom_text))
async def smm_dm_custom_text(msg: Message, state: FSMContext):
    await state.update_data(dm_text=msg.text.strip()[:200])
    await start_smm_execution(msg, state, msg.from_user.id)

@dp.message(StateFilter(SMMBuyFlow.waiting_channel_link))
async def smm_channel_link(msg: Message, state: FSMContext):
    await state.update_data(channel_link=msg.text.strip())
    data = await state.get_data()
    
    if data['service'] in ["votes", "vote_poll", "reactions"]:
        await msg.answer("🔗 Now, send the direct Post Link:")
        await state.set_state(SMMBuyFlow.waiting_post_link)
    else:
        await start_smm_execution(msg, state, msg.from_user.id)

@dp.message(StateFilter(SMMBuyFlow.waiting_post_link))
async def smm_post_link(msg: Message, state: FSMContext):
    post_link = msg.text.strip()
    await state.update_data(post_link=post_link)
    data = await state.get_data()
    service = data['service']

    if service == "votes":
        await msg.answer("🔘 <b>Which button do you want to click?</b>\nSend the number (e.g., send <code>1</code> for the first button, <code>2</code> for the second):", parse_mode="HTML")
        await state.set_state(SMMBuyFlow.waiting_vote_button)
        
    elif service == "vote_poll":
        # === PRE-FLIGHT: IMPORT POLL OPTIONS ===
        status = await msg.answer("🔄 <i>Importing poll from Telegram...</i>", parse_mode="HTML")
        session_doc = numbers_col.find_one({"status": "healthy", "used": False})
        
        if not session_doc:
            return await status.edit_text("❌ No sessions available to fetch the poll.")
            
        phone = session_doc["number"]
        session_path = f"temp_sessions/preflight_{phone}_{int(time.time())}"
        load_session_from_db(phone, session_path)
        
        client = TelegramClient(session_path, int(os.getenv("API_ID")), os.getenv("API_HASH"))
        poll_options = []
        
        try:
            await client.connect()
            channel_link = data['channel_link']
            # Join channel to view private polls
            if "+" in channel_link or "joinchat" in channel_link:
                hash_str = channel_link.split("/")[-1].replace("+", "")
                await client(ImportChatInviteRequest(hash_str))
            else:
                await client(JoinChannelRequest(channel_link))
                
            # Parse link
            parts = post_link.strip("/").split("/")
            msg_id = int(parts[-1])
            peer = int("-100" + parts[-2]) if parts[-3] == "c" else parts[-2]
            
            entity = await client.get_entity(peer)
            msgs = await client.get_messages(entity, ids=[msg_id])
            
            if msgs and msgs[0] and msgs[0].poll:
                for i, answer in enumerate(msgs[0].poll.poll.answers):
                    # We store the exact bytes Telegram needs for this option
                    poll_options.append((i, answer.text))
        except Exception as e:
            print(f"Poll Pre-flight error: {e}")
        finally:
            if client.is_connected(): await client.disconnect()
            if os.path.exists(f"{session_path}.session"): os.remove(f"{session_path}.session")

        if not poll_options:
            return await status.edit_text("❌ Could not read the poll. Ensure the link is correct and it is an active poll.")

        kb = InlineKeyboardBuilder()
        for idx, text in poll_options:
            kb.row(InlineKeyboardButton(text=text, callback_data=f"smm_p_opt:{idx}"))
        
        await status.edit_text("📊 <b>Poll Imported!</b>\nSelect which option you want the bots to vote for:", reply_markup=kb.as_markup(), parse_mode="HTML")
        await state.set_state(SMMBuyFlow.waiting_poll_option)
        
    else:
        await start_smm_execution(msg, state, msg.from_user.id)

@dp.message(StateFilter(SMMBuyFlow.waiting_vote_button))
async def smm_vote_button_input(msg: Message, state: FSMContext):
    if not msg.text.isdigit():
        return await msg.answer("❌ Please send a valid number.")
    # Subtract 1 because Telethon uses 0-based indexing for buttons
    await state.update_data(button_index=int(msg.text.strip()) - 1)
    await start_smm_execution(msg, state, msg.from_user.id)

@dp.callback_query(StateFilter(SMMBuyFlow.waiting_poll_option), F.data.startswith("smm_p_opt:"))
async def smm_poll_option_input(cq: CallbackQuery, state: FSMContext):
    await state.update_data(poll_option_index=int(cq.data.split(":")[1]))
    await cq.message.edit_text("✅ Option selected.")
    await start_smm_execution(cq.message, state, cq.from_user.id)
    await cq.answer()


# ================= Execution Engine =================
async def start_smm_execution(msg: Message, state: FSMContext, user_id: int):
    data = await state.get_data()
    service = data['service']
    qty = int(data['qty'])
    
    settings = smm_col.find_one({"service": service})
    total_price = qty * settings.get("price", 2.0)
    
    user = users_col.find_one({"_id": user_id})
    if user.get("balance", 0) < total_price:
        await msg.answer("❌ Insufficient balance. Task cancelled.")
        return await state.clear()
        
    sessions = list(numbers_col.find({"status": "healthy", "used": False}).limit(qty))
    if len(sessions) < qty:
        await msg.answer("❌ Stock dropped. Task cancelled.")
        return await state.clear()
        
    # Deduct balance securely
    users_col.update_one({"_id": user_id}, {"$inc": {"balance": -total_price}})

    status_msg = await msg.answer("⏳ <b>Task Started... Processing SMM...</b>\n<i>You can continue using the bot.</i>", parse_mode="HTML")
    await state.clear() 
    
    # Run background task
    asyncio.create_task(run_telethon_smm_task(
        user_id=user_id,
        service=service,
        qty=qty,
        total_price=total_price,
        data=data,
        sessions=sessions,
        status_msg=status_msg
    ))

async def run_telethon_smm_task(user_id, service, qty, total_price, data, sessions, status_msg: Message):
    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")
    
    success_count = 0
    start_time = time.time()
    
    # Parse Links & Peers Safely
    channel_link = data.get("channel_link", "")
    post_link = data.get("post_link", "").strip()
    
    msg_id = 0
    peer = None
    
    if post_link:
        parts = post_link.strip("/").split("/")
        msg_id = int(parts[-1]) if parts[-1].isdigit() else 0
        if len(parts) >= 3 and parts[-3] == "c":
            peer = int("-100" + parts[-2])
        elif len(parts) >= 2:
            peer = parts[-2]

    # Random DM Texts
    random_texts = [
        "Hey, how are you doing today?",
        "Hello! Nice to connect.",
        "Hi there! Have a great day ahead.",
        "Hey! What's up?",
        "Greetings! Hope you are well."
    ]

    for s_doc in sessions:
        phone = s_doc["number"]
        session_path = f"temp_sessions/smm_{phone}_{int(time.time())}"
        os.makedirs("temp_sessions", exist_ok=True)
        
        if not load_session_from_db(phone, session_path):
            continue

        client = TelegramClient(session_path, api_id, api_hash)
        
        try:
            await client.connect()
            if not await client.is_user_authorized():
                continue
            
            # --- 1. JOIN CHANNEL (Required for Votes, Polls, Reactions, Joins) ---
            if service in ["joins", "votes", "vote_poll", "reactions"]:
                try:
                    if "+" in channel_link or "joinchat" in channel_link:
                        hash_str = channel_link.split("/")[-1].replace("+", "")
                        await client(ImportChatInviteRequest(hash_str))
                    else:
                        await client(JoinChannelRequest(channel_link))
                except Exception:
                    pass # Ignore if already joined
            
            # --- 2. GET ENTITY (Required for post interactions) ---
            entity = None
            if service in ["votes", "vote_poll", "reactions", "views"]:
                entity = await client.get_entity(peer)

            # --- 3. EXECUTE SERVICE ---
            if service == "joins":
                success_count += 1

            elif service == "views":
                await client(GetMessagesViewsRequest(peer=entity, id=[msg_id], increment=True))
                success_count += 1

            elif service == "reactions":
                # 1. Define emoji sets
                happy_emojis = ['❤️', '🔥', '👍', '🎉', '🥰']
                sad_emojis = ['👎', '🤮', '🖕', '😂']
                
                # 2. Select the list based on user choice
                target_emojis = happy_emojis if data.get("reaction_type") == "happy" else sad_emojis
                
                # 3. Pick emoji using modulo (%) to distribute equally across sessions
                # Example: If 10 sessions and 5 emojis, each emoji hits 2 times.
                emo = target_emojis[success_count % len(target_emojis)]
                
                await client(SendReactionRequest(
                    peer=entity, 
                    msg_id=msg_id, 
                    reaction=[ReactionEmoji(emoticon=emo)]
                ))
                success_count += 1
            

            elif service == "votes":
                # High-level inline button clicker
                btn_idx = data.get("button_index", 0)
                msgs = await client.get_messages(entity, ids=[msg_id])
                if msgs and msgs[0]:
                    await msgs[0].click(btn_idx)
                    success_count += 1

            elif service == "vote_poll":
                opt_idx = data.get("poll_option_index", 0)
                msgs = await client.get_messages(entity, ids=[msg_id])
                if msgs and msgs[0] and msgs[0].poll:
                    options = msgs[0].poll.poll.answers
                    if opt_idx < len(options):
                        # Telethon handles the exact byte payload needed for the option
                        await client(SendVoteRequest(peer=entity, msg_id=msg_id, options=[options[opt_idx].option]))
                        success_count += 1
                
            elif service == "mass_dm":
                target = data.get("dm_target")
                text_to_send = random.choice(random_texts) if data.get("dm_text") == "random" else data.get("dm_text")
                await client.send_message(target, text_to_send)
                success_count += 1

        except Exception as e:
            print(f"SMM Error on {phone} ({service}): {e}")
            
        finally:
            if client.is_connected():
                await client.disconnect()
            if os.path.exists(f"{session_path}.session"):
                os.remove(f"{session_path}.session") # Clean up local storage
        
        # Anti-flood sleep
        await asyncio.sleep(1.5)

    # Compile Reports
    end_time = time.time()
    time_taken = round((end_time - start_time) / 60, 2)
    
    user_msg = (
        f"✅ <b>SMM Task Completed!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🛠️ <b>Service:</b> {service.replace('_', ' ').title()}\n"
        f"📦 <b>Requested:</b> {qty}\n"
        f"⏱️ <b>Time Taken:</b> {time_taken} mins\n"
        f"💰 <b>Cost:</b> {fmt_curr(total_price)}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    
    try:
        await bot.edit_message_text(chat_id=user_id, message_id=status_msg.message_id, text=user_msg, parse_mode="HTML")
    except Exception:
        await bot.send_message(user_id, user_msg, parse_mode="HTML")

    log_msg = (
        f"🚀 <b>New SMM Order Processed</b>\n"
        f"User ID: <code>{user_id}</code>\n"
        f"Service: <b>{service.replace('_', ' ').title()}</b>\n"
        f"Quantity: {qty} (Success: {success_count})\n"
        f"Paid: {fmt_curr(total_price)}"
    )
    try:
        await bot.send_message(-1003208353049, log_msg, parse_mode="HTML")
    except:
        pass




# ================= /sales Command =================
@dp.message(Command("sales"))
async def cmd_sales(msg: Message):
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ You are not authorized to view sales report.")

    now = datetime.utcnow()
    start_of_week = now - timedelta(days=now.weekday())
    start_of_day = datetime(now.year, now.month, now.day)
    # Collections assumed
    users_col = db["users"]
    orders_col = db["orders"]
    recharges_col = db["recharges"]  # If you track top-ups

    # Bot Status
    bot_status = "🟢 Active"

    # Total users
    total_users = users_col.count_documents({})

    # All sales
    all_orders = list(orders_col.find({"status": "purchased"}))
    total_numbers_sold = len(all_orders)
    total_earnings = sum(order.get("price", 0) for order in all_orders)
    avg_price = total_earnings / total_numbers_sold if total_numbers_sold else 0

    # Top Country overall
    from collections import Counter
    country_counts = Counter(order.get("country", "Unknown") for order in all_orders)
    top_country = country_counts.most_common(1)[0][0] if country_counts else "N/A"

    # Total Recharge
    total_recharge = sum(txn.get("amount", 0) for txn in recharges_col.find({}))

    # ================= WEEKLY =================
    week_orders = list(orders_col.find({
        "status": "purchased",
        "date": {"$gte": start_of_week}
    }))
    week_sales = sum(o.get("price", 0) for o in week_orders)
    week_count = len(week_orders)
    week_avg = week_sales / week_count if week_count else 0
    week_country_counts = Counter(o.get("country", "Unknown") for o in week_orders)
    week_top_country = week_country_counts.most_common(1)[0][0] if week_country_counts else "N/A"
    week_recharge = sum(txn.get("amount", 0) for txn in recharges_col.find({"date": {"$gte": start_of_week}}))

    # ================= DAILY =================
    day_orders = list(orders_col.find({
        "status": "purchased",
        "date": {"$gte": start_of_day}
    }))
    day_sales = sum(o.get("price", 0) for o in day_orders)
    day_count = len(day_orders)
    day_avg = day_sales / day_count if day_count else 0
    day_country_counts = Counter(o.get("country", "Unknown") for o in day_orders)
    day_top_country = day_country_counts.most_common(1)[0][0] if day_country_counts else "N/A"
    day_recharge = sum(txn.get("amount", 0) for txn in recharges_col.find({"date": {"$gte": start_of_day}}))

    # ================= REPORT =================
    report = (
        "📊 <b>Bot Profit Report</b>\n"
        f"<b>⚙️ Bot Status: </b>{bot_status}\n\n"
        f"<b>👥 Total Users: </b>{total_users}\n"
        f"<b>🔢 Total Numbers Sold: </b>{total_numbers_sold}\n"
        f"💰 Total Sales: ₹{total_earnings:.2f}\n"
        f"⚖️ Avg Price/Number: ₹{avg_price:.2f}\n"
        f"🌍 Top Country: {top_country}\n"
        f"💳 Total Recharge: ₹{total_recharge:.2f}\n\n"
    )

    await msg.answer(report, parse_mode="HTML")

@dp.message(Command("report"))
async def cmd_report(msg: Message):
    # Security check: Only admins can use this
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ Not authorized.")

    # High UI status message while the bot calculates
    status_msg = await msg.answer("🔄 <i>Generating full statistics report...</i>", parse_mode="HTML")

    try:
        # 1. Bot Status
        bot_status = "🟢 Active"

        # 2. Total Unsold Sessions
        total_unsold = numbers_col.count_documents({"used": False})

        # 3. Database Storage (MongoDB dbstats logic)
        db_stats = db.command("dbstats")
        db_size_mb = db_stats.get("dataSize", 0) / (1024 * 1024)

        # 4. Country Stats & Stock Worth calculations
        countries = list(countries_col.find({}))
        lowest_country, highest_country = "N/A", "N/A"
        lowest_price = float('inf')
        highest_price = 0
        stock_worth = 0.0

        for c in countries:
            # We base highest/lowest off the 'Healthy' price tier
            h_price = c.get("price_healthy", 0)
            
            if h_price > 0 and h_price < lowest_price:
                lowest_price = h_price
                lowest_country = c.get("name")
                
            if h_price > highest_price:
                highest_price = h_price
                highest_country = c.get("name")

            # Calculate total worth of all unsold stock inside this specific country
            worth_h = c.get("stock_healthy", 0) * c.get("price_healthy", 0)
            worth_ts = c.get("stock_temp_spam", 0) * c.get("price_temp_spam", 0)
            worth_ps = c.get("stock_perm_spam", 0) * c.get("price_perm_spam", 0)
            worth_fz = c.get("stock_frozen", 0) * c.get("price_frozen", 0)
            
            stock_worth += (worth_h + worth_ts + worth_ps + worth_fz)

        if lowest_price == float('inf'): lowest_price = 0

        # Set up timezone boundaries for "Today's" metrics
        now = datetime.now(timezone.utc)
        start_of_day = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

        def get_dt(doc):
            """Helper to extract date safely from DB docs regardless of field name"""
            dt = doc.get("created_at") or doc.get("date")
            if isinstance(dt, datetime):
                return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
            return None

        # 5. Sales Data (Purchased Orders)
        all_orders = list(orders_col.find({"status": "purchased"}))
        total_sales = sum(o.get("price", 0) for o in all_orders)
        
        todays_orders = [o for o in all_orders if get_dt(o) and get_dt(o) >= start_of_day]
        todays_sales = sum(o.get("price", 0) for o in todays_orders)

        # 6. Recharge Data
        txns_col = db["transactions"]
        # Look for successful recharge statuses
        all_txns = list(txns_col.find({"status": {"$in": ["paid", "success", "completed"]}}))
        total_recharge = sum(t.get("amount", 0) for t in all_txns)
        
        todays_txns = [t for t in all_txns if get_dt(t) and get_dt(t) >= start_of_day]
        todays_recharge = sum(t.get("amount", 0) for t in todays_txns)

        # 7. Generate Final Output Message
        report_text = (
            f"📊 <b>Bot Full Statistics Report</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚙️ <b>Bot Status:</b> {bot_status}\n\n"
            f"📦 <b>Total Unsold Sessions:</b> {total_unsold}\n"
            f"🗄️ <b>Database Storage:</b> {db_size_mb:.2f} MB\n"
            f"📉 <b>Lowest Priced Country:</b> {lowest_country} ({fmt_curr(lowest_price)})\n"
            f"📈 <b>Highest Priced Country:</b> {highest_country} ({fmt_curr(highest_price)})\n\n"
            f"💰 <b>Total Sales:</b> {fmt_curr(total_sales)}\n"
            f"💸 <b>Today's Sales:</b> {fmt_curr(todays_sales)}\n"
            f"💳 <b>Total Recharge:</b> {fmt_curr(total_recharge)}\n"
            f"⚡ <b>Today's Recharge:</b> {fmt_curr(todays_recharge)}\n"
            f"💎 <b>Total Stock Worth:</b> {fmt_curr(stock_worth)}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )

        await status_msg.edit_text(report_text, parse_mode="HTML")

    except Exception as e:
        await status_msg.edit_text(f"❌ <b>Error generating report:</b> <code>{str(e)}</code>", parse_mode="HTML")
        

@dp.message(Command("sellcountry"))
async def add_sell_countries(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("Unauthorized ❌")

    # Remove the command itself and split lines
    lines = msg.text.split("\n")[1:]  # Skip the first line (the command)
    if not lines:
        return await msg.answer(
            "📋 Send like this:\n\n"
            "<code>/sellcountry\n+91 India ₹30\n+1 USA ₹32\n+62 Indonesia ₹28</code>",
            parse_mode="HTML"
        )

    updated = []
    errors = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        try:
            parts = line.split(" ")
            prefix = parts[0]
            if not prefix.startswith("+"):
                raise ValueError("Missing +country code")

            # Extract price (₹XX)
            match_price = [p for p in parts if "₹" in p]
            if not match_price:
                raise ValueError("Missing price (₹)")
            price = match_price[-1]  # Take last ₹ value
            country = " ".join(parts[1:parts.index(price)]).strip()

            db["sell_countries"].update_one(
                {"prefix": prefix},
                {"$set": {"country": country, "price": price}},
                upsert=True
            )

            updated.append(f"{prefix} {country} → {price}")
        except Exception as e:
            errors.append(f"❌ {line} ({e})")

    text = ""
    if updated:
        text += "✅ <b>Updated Successfully:</b>\n" + "\n".join(updated) + "\n\n"
    if errors:
        text += "⚠️ <b>Errors:</b>\n" + "\n".join(errors)

    await msg.answer(text or "⚙️ Nothing processed.", parse_mode="HTML")


# ================= Admin Credit/Debit Commands =================
@dp.message(Command("credit"))
async def cmd_credit(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ Not authorized.")
    
    await msg.answer("💰 Send user ID and amount to credit separated by a comma (e.g., 123456789,50):")
    await state.set_state("credit_waiting")

@dp.message(StateFilter("credit_waiting"))
async def handle_credit(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return

    if "," not in msg.text:
        return await msg.answer("❌ Invalid format. Example: 123456789,50")

    user_id_str, amount_str = msg.text.split(",", 1)
    try:
        user_id = int(user_id_str.strip())
        amount = float(amount_str.strip())
    except ValueError:
        return await msg.answer("❌ Invalid user ID or amount format.")

    user = users_col.find_one({"_id": user_id})
    if not user:
        return await msg.answer(f"❌ User with ID {user_id} not found.")

    new_balance = user.get("balance", 0.0) + amount
    users_col.update_one({"_id": user_id}, {"$set": {"balance": new_balance}})
    await msg.answer(f"✅ Credited ₹{amount:.2f} to {user.get('username') or user_id}\n💰 New Balance: ₹{new_balance:.2f}")
    await state.clear()


@dp.message(Command("debit"))
async def cmd_debit(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ Not authorized.")
    
    await msg.answer("💸 Send user ID and amount to debit separated by a comma (e.g., 123456789,50):")
    await state.set_state("debit_waiting")

@dp.message(StateFilter("debit_waiting"))
async def handle_debit(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return

    if "," not in msg.text:
        return await msg.answer("❌ Invalid format. Example: 123456789,50")

    user_id_str, amount_str = msg.text.split(",", 1)
    try:
        user_id = int(user_id_str.strip())
        amount = float(amount_str.strip())
    except ValueError:
        return await msg.answer("❌ Invalid user ID or amount format.")

    user = users_col.find_one({"_id": user_id})
    if not user:
        return await msg.answer(f"❌ User with ID {user_id} not found.")

    new_balance = max(user.get("balance", 0.0) - amount, 0.0)
    users_col.update_one({"_id": user_id}, {"$set": {"balance": new_balance}})
    await msg.answer(f"✅ Debited ₹{amount:.2f} from {user.get('username') or user_id}\n💰 New Balance: ₹{new_balance:.2f}")
    await state.clear()





    # ================= MongoDB Redeem Collection =================
redeem_col = db["redeem_codes"]  # Add this at top with other collections

# ================= Redeem FSM =================
class RedeemState(StatesGroup):
    # For auto-generated redeem codes
    waiting_amount = State()          # Admin enters amount
    waiting_limit = State()           # Admin selects max users via inline numeric keypad

    # For custom redeem codes
    waiting_code = State()            # Admin enters custom code (e.g. DIWALI100)
    waiting_amount_custom = State()   # Admin enters amount for custom code
    waiting_limit_custom = State()    # Admin selects max users for custom code

class UserRedeemState(StatesGroup):
    waiting_code = State()            # User enters redeem code
    
# ================= Helper =================
import random, string
def generate_code(length=8):
    """Generate code like HEIKE938"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))



    
        # ================= Admin: Create Custom Redeem =================
@dp.message(Command("cusredeem"))
async def cmd_custom_redeem(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ Not authorized.")
    await msg.answer("🎟️ Enter the custom redeem code (e.g. DIWALI100):")
    await state.set_state(RedeemState.waiting_code)

# ================= Admin: Handle Custom Code =================
@dp.message(StateFilter(RedeemState.waiting_code))
async def handle_custom_code(msg: Message, state: FSMContext):
    code = msg.text.strip().upper()
    if redeem_col.find_one({"code": code}):
        return await msg.answer("⚠️ This code already exists. Try another one.")

    await state.update_data(custom_code=code)
    await msg.answer("💰 Enter the amount for this redeem code:")
    await state.set_state(RedeemState.waiting_amount_custom)

# ================= Admin: Handle Custom Amount =================
@dp.message(StateFilter(RedeemState.waiting_amount_custom))
async def handle_custom_amount(msg: Message, state: FSMContext):
    try:
        amount = float(msg.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        return await msg.answer("❌ Invalid amount. Send a number like 50 or 100.")

    await state.update_data(amount=amount, limit_str="")

    # Inline numeric keypad
    kb = InlineKeyboardBuilder()
    for row in (("1", "2", "3"), ("4", "5", "6"), ("7", "8", "9"), ("0", "❌", "✅")):
        kb.row(*[InlineKeyboardButton(text=btn, callback_data=f"cusredeemnum:{btn}") for btn in row])

    await msg.answer(
        "👥 Select max number of users who can claim this custom code:\n<b>0</b>",
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )
    await state.set_state(RedeemState.waiting_limit_custom)

# ================= Admin: Handle Custom Inline Number Pad =================
@dp.callback_query(F.data.startswith("cusredeemnum:"))
async def handle_custom_redeem_number(cq: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current = data.get("limit_str", "")
    value = cq.data.split(":")[1]

    if value == "❌":
        current = current[:-1]
    elif value == "✅":
        if not current:
            await cq.answer("❌ Please select at least one user.", show_alert=True)
            return
        try:
            limit = int(current)
        except ValueError:
            await cq.answer("❌ Invalid number.", show_alert=True)
            return

        code = data.get("custom_code")
        amount = data.get("amount")
        created_at = datetime.utcnow()

        # Insert redeem into MongoDB
        redeem_col.insert_one({
            "code": code,
            "amount": amount,
            "max_claims": limit,
            "claimed_count": 0,
            "claimed_users": [],
            "created_at": created_at
        })

        await cq.message.edit_text(
            f"✅ Custom redeem code created!\n\n"
            f"🎟️ Code: <code>{code}</code>\n"
            f"💰 Amount: ₹{amount:.2f}\n"
            f"👥 Max Claims: {limit}",
            parse_mode="HTML"
        )
        await state.clear()
        return
    else:
        current += value
        if len(current) > 6:
            current = current[:6]

    await state.update_data(limit_str=current)

    # Rebuild keypad dynamically
    kb = InlineKeyboardBuilder()
    for row in (("1", "2", "3"), ("4", "5", "6"), ("7", "8", "9"), ("0", "❌", "✅")):
        kb.row(*[InlineKeyboardButton(text=btn, callback_data=f"cusredeemnum:{btn}") for btn in row])

    await cq.message.edit_text(
        f"👥 Select max number of users who can claim this custom code:\n<b>{current or '0'}</b>",
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )
    await cq.answer()
        


# ================= Admin: View Redeems =================
@dp.message(Command("redeemlist"))
async def cmd_redeem_list(msg: Message):
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ Not authorized.")

    redeems = list(redeem_col.find())
    if not redeems:
        return await msg.answer("📭 No redeem codes found.")

    text = "🎟️ <b>Active Redeem Codes:</b>\n\n"
    for r in redeems:
        text += (
            f"Code: <code>{r['code']}</code>\n"
            f"💰 Amount: ₹{r['amount']}\n"
            f"👥 {r['claimed_count']} / {r['max_claims']} claimed\n\n"
        )
    await msg.answer(text, parse_mode="HTML")

# ================= User: Redeem Code =================
@dp.callback_query(F.data == "redeem")
async def callback_user_redeem(cq: CallbackQuery, state: FSMContext):
    await cq.answer("✅ Send your redeem code now!", show_alert=False)
    await cq.message.answer("🎟️ Send your redeem code below:")
    await state.set_state(UserRedeemState.waiting_code)

# Command /redeem
@dp.message(F.text == "/redeem")
async def command_user_redeem(message: Message, state: FSMContext):
    await message.answer("✅ Send your redeem code now!")
    await message.answer("🎟️ Send your redeem code below:")
    await state.set_state(UserRedeemState.waiting_code)

@dp.message(StateFilter(UserRedeemState.waiting_code))
async def handle_user_redeem(msg: Message, state: FSMContext):
    code = msg.text.strip().upper()
    redeem = redeem_col.find_one({"code": code})

    if not redeem:
        await msg.answer("❌ Invalid or expired redeem code.")
        return await state.clear()

    if redeem["claimed_count"] >= redeem["max_claims"]:
        await msg.answer("🚫 This code has reached its claim limit.")
        return await state.clear()

    user = users_col.find_one({"_id": msg.from_user.id})
    if not user:
        await msg.answer("⚠️ Please use /start first.")
        return await state.clear()

    if msg.from_user.id in redeem.get("claimed_users", []):
        await msg.answer("⚠️ You have already claimed this code.")
        return await state.clear()

    # Credit user balance
    users_col.update_one({"_id": msg.from_user.id}, {"$inc": {"balance": redeem["amount"]}})
    redeem_col.update_one(
        {"code": code},
        {"$inc": {"claimed_count": 1}, "$push": {"claimed_users": msg.from_user.id}}
    )

    await msg.answer(
        f"✅ Code <b>{code}</b> redeemed successfully!\n💰 You received ₹{redeem['amount']:.2f}",
        parse_mode="HTML"
    )
    await state.clear()

@dp.message(Command("editsell"))
async def cmd_editsell(msg: Message):
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ Not authorized.")

    await msg.answer("📋 Send the list in format:\n\n<code>USA ₹50\nIndia ₹10\nUK ₹20</code>")

    @dp.message()  # Next message from admin
    async def handle_sell_edit(m: Message):
        sell_prices_col.delete_many({})
        for line in m.text.splitlines():
            try:
                parts = line.split("₹")
                country = parts[0].strip()
                price = float(parts[1].strip())
                code = "+1" if "USA" in country else "+91" if "India" in country else ""  # add more or editable
                sell_rates_col.insert_one({"country": country, "price": price, "code": code})
            except:
                continue
        await m.answer("✅ Sell rates updated.")

# ================= Admin Live Credits =================
@dp.message(Command("livecredits"))
async def cmd_livecredits(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    await show_live_credits(msg, page=0)

async def show_live_credits(msg_or_call, page: int):
    limit = 10
    skip = page * limit
    
    # Find users with balance > 0, sort DESC by balance
    cursor = users_col.find({"balance": {"$gt": 0}}).sort("balance", -1)
    total_users = users_col.count_documents({"balance": {"$gt": 0}})
    
    users_list = list(cursor.skip(skip).limit(limit))
    
    if not users_list:
        text = "📉 No users currently have a positive balance."
        kb = None
    else:
        text = f"💰 <b>Live Credits (Page {page+1})</b>\n\n"
        for u in users_list:
            u_link = f"<a href='tg://user?id={u['_id']}'>{u.get('username') or u['_id']}</a>"
            text += f"👤 {u_link} : <code>₹{u['balance']:.2f}</code>\n"
            
        kb = InlineKeyboardBuilder()
        if page > 0:
            kb.button(text="⬅️ Prev", callback_data=f"livecredits:{page-1}")
        if (skip + limit) < total_users:
            kb.button(text="Next ➡️", callback_data=f"livecredits:{page+1}")
        kb.adjust(2)
        kb.row(InlineKeyboardButton(text="❌ Close", callback_data="delete_msg"))

    if isinstance(msg_or_call, Message):
        await msg_or_call.answer(text, parse_mode="HTML", reply_markup=kb.as_markup() if kb else None)
    else:
        await msg_or_call.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup() if kb else None)

@dp.callback_query(F.data.startswith("livecredits:"))
async def pagination_livecredits(cq: CallbackQuery):
    if not is_admin(cq.from_user.id):
        return await cq.answer("❌", show_alert=True)
    page = int(cq.data.split(":")[1])
    await show_live_credits(cq, page)
    await cq.answer()

@dp.callback_query(F.data == "delete_msg")
async def delete_this_msg(cq: CallbackQuery):
    await cq.message.delete()

# ================= User History & Logs =================

@dp.callback_query(F.data == "history")
async def show_user_history(cq: CallbackQuery):
    user_id = cq.from_user.id
    
    # 1. Calculate Total Recharged
    # Note: Assuming 'transactions' collection is used for recharges based on your file
    txns = list(db["transactions"].find({"user_id": user_id, "status": "paid"})) # Or "success" check your recharge_flow
    total_added = sum(t.get("amount", 0) for t in txns)
    
    # 2. Calculate Purchases
    orders = list(orders_col.find({"user_id": user_id, "status": "purchased"}))
    total_purchased = len(orders)
    total_spent = sum(o.get("price", 0) for o in orders)
    
    text = (
        f"📜 <b>User History</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🛍️ <b>Accounts Bought:</b> {total_purchased}\n"
        f"💸 <b>Total Spent:</b> ₹{total_spent:.2f}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📂 View Purchase Logs", callback_data="purchase_logs:0"))
    kb.row(InlineKeyboardButton(text="🔙 Back", callback_data="back_main")) # Back to profile/stats
    
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())


@dp.callback_query(F.data.startswith("purchase_logs:"))
async def show_purchase_logs(cq: CallbackQuery):
    user_id = cq.from_user.id
    page = int(cq.data.split(":")[1])
    limit = 10
    skip = page * limit
    
    # Fetch orders sorted by newest first
    cursor = orders_col.find({"user_id": user_id, "status": "purchased"}).sort("_id", -1)
    total_orders = orders_col.count_documents({"user_id": user_id, "status": "purchased"})
    
    my_orders = list(cursor.skip(skip).limit(limit))
    
    if not my_orders:
        return await cq.answer("❌ No purchase history found.", show_alert=True)
    
    text = f"📂 <b>Purchase Logs (Page {page+1})</b>\n\n"
    
    for order in my_orders:
        ph_number = order.get('number')
        
        # Try to find password in numbers_col
        # Note: If you delete numbers from DB after sell, this might return None.
        # But usually, 'used=True' numbers stay in DB.
        num_doc = numbers_col.find_one({"number": ph_number})
        password = num_doc.get("password") if num_doc else "N/A"
        if not password: password = "None"
        
        text += (
            f"📱 <b>{ph_number}</b>\n"
            f"🔐 Pass: <code>{password}</code>\n"
            f"-------------------\n"
        )
        
    kb = InlineKeyboardBuilder()
    
    # Navigation
    nav_btns = []
    if page > 0:
        nav_btns.append(InlineKeyboardButton(text="⬅️", callback_data=f"purchase_logs:{page-1}"))
    if (skip + limit) < total_orders:
        nav_btns.append(InlineKeyboardButton(text="➡️", callback_data=f"purchase_logs:{page+1}"))
        
    if nav_btns:
        kb.row(*nav_btns)
        
    kb.row(InlineKeyboardButton(text="🔙 Back to History", callback_data="history"))
    
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    

# ================= Admin Ban Commands (Upgraded) =================
async def get_target_id(msg: Message, args: list) -> int | None:
    """Helper to get user ID from reply, username, or manual ID"""
    # 1. Check if it's a reply
    if msg.reply_to_message:
        return msg.reply_to_message.from_user.id
    
    # 2. Check if an ID or @username was provided
    if len(args) < 2:
        return None
    
    target = args[1]
    
    # If it's a numeric ID
    if target.isdigit():
        return int(target)
    
    # If it's a username (this only works if the user is already in your DB)
    if target.startswith("@"):
        username = target.replace("@", "")
        user_doc = users_col.find_one({"username": username})
        if user_doc:
            return user_doc["_id"]
    
    return None



# ================= 1. /check Command =================
@dp.message(Command("check"))
async def cmd_check_sessions(msg: Message):
    if not is_admin(msg.from_user.id): return
    total_unsold = numbers_col.count_documents({"used": False})
    
    kb = InlineKeyboardBuilder()
    for c in countries_col.find({}):
        kb.button(text=c['name'], callback_data=f"chk_cntry:{c['name']}")
    kb.adjust(2)
    
    await msg.answer(
        f"📊 <b>Current active unsold sessions:</b> {total_unsold}\n\n"
        f"Select country you wanna run check for:",
        parse_mode="HTML", reply_markup=kb.as_markup()
    )

# ================= 2. Run Spambot Check =================
@dp.callback_query(F.data.startswith("chk_cntry:"))
async def run_check_country(cq: CallbackQuery, state: FSMContext):
    country = cq.data.split(":")[1]
    sessions = list(numbers_col.find({"country": country, "used": False}))
    
    if not sessions:
        return await cq.answer("❌ No unsold sessions in this country.", show_alert=True)
    
    status_msg = await cq.message.edit_text(f"🔄 <b>Checking {len(sessions)} sessions for {country}...\nExecution time: 1-5 mins...</b>", parse_mode="HTML")
    
    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")
    
    results = {"healthy": [], "temp_spam": [], "perm_spam": [], "frozen": [], "dead": []}
    os.makedirs("temp_check", exist_ok=True)
    
    paths = []
    for s in sessions:
        phone = s["number"]
        path = f"temp_check/{phone}_{int(time.time())}"
        load_session_from_db(phone, path)
        paths.append((path, s))
        
    for path, s in paths:
        await check_acc(path, api_id, api_hash, results) # Uses your existing bulk /add checker
        
    await state.update_data(check_results=results, check_country=country, check_sessions=sessions)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Add Healthy to Healthy", callback_data="chk_action:healthy")],
        [InlineKeyboardButton(text="🗑 Move Spam to Spam", callback_data="chk_action:spam")],
        [InlineKeyboardButton(text="🌍 Move Freeze to another country", callback_data="chk_action:freeze")],
        [InlineKeyboardButton(text="🔓 Remove 2FA", callback_data="chk_action:rm2fa"),
         InlineKeyboardButton(text="🔐 Change 2FA", callback_data="chk_action:ch2fa")]
    ])
    
    text = (
        f"✅ <b>Check Complete for {country}</b>\n\n"
        f"🟢 Healthy: {len(results['healthy'])}\n"
        f"🟡 Temp Spam: {len(results['temp_spam'])}\n"
        f"🔴 Perm Spam: {len(results['perm_spam'])}\n"
        f"❄️ Frozen: {len(results['frozen'])}\n"
        f"💀 Dead: {len(results['dead'])}\n\n"
        f"<i>Select an action below:</i>"
    )
    
    await status_msg.edit_text(text, reply_markup=kb, parse_mode="HTML")

# ================= 3. Button Actions =================
@dp.callback_query(F.data.startswith("chk_action:"))
async def chk_action_handler(cq: CallbackQuery, state: FSMContext):
    action = cq.data.split(":")[1]
    data = await state.get_data()
    res = data.get("check_results")
    country = data.get("check_country")
    
    if action == "healthy":
        if not res["healthy"]:
            return await cq.answer("No healthy sessions to update.", show_alert=True)
            
        updated = 0
        for path in res["healthy"]:
            # Extract phone from temp path (temp_check/PHONE_TIMESTAMP)
            phone = path.split("/")[-1].split("_")[0]
            session_file_path = f"{path}.session"
            
            if os.path.exists(session_file_path):
                with open(session_file_path, "rb") as f:
                    session_data = Binary(f.read())
                
                # Update status and session file in DB
                numbers_col.update_one(
                    {"number": phone}, 
                    {"$set": {
                        "status": "healthy", 
                        "session_file": session_data, 
                        "used": False
                    }}
                )
                updated += 1
                
                # Cleanup temp file
                try: os.remove(session_file_path)
                except: pass
        
        recount_stock(country) # Sync stock counts
        await cq.message.answer(
            f"✅ <b>Healthy sessions updated!</b>\n"
            f"{updated} sessions confirmed and saved as Healthy for {country}.", 
            parse_mode="HTML"
        )
        await cq.answer()

    elif action == "spam":
        # ... your existing spam code ...
        moved = 0
        for p in res["temp_spam"]:
            phone = p.split("/")[-1].split("_")[0]
            numbers_col.update_one({"number": phone}, {"$set": {"status": "temp_spam"}})
            moved += 1
        for p in res["perm_spam"]:
            phone = p.split("/")[-1].split("_")[0]
            numbers_col.update_one({"number": phone}, {"$set": {"status": "perm_spam"}})
            moved += 1
            
        recount_stock(country)
        await cq.message.answer(f"✅ <b>Spam moved successfully!</b>\n{moved} sessions sent to Spam categories for {country}.", parse_mode="HTML")
        await cq.answer()
        
    # ... rest of your existing elif blocks (freeze, rm2fa, ch2fa) ...
    
        
    elif action == "freeze":
        if not res["frozen"]:
            return await cq.answer("No frozen sessions to move.", show_alert=True)
        kb = InlineKeyboardBuilder()
        for c in countries_col.find({}):
            kb.button(text=c['name'], callback_data=f"chk_freeze_to:{c['name']}")
        kb.adjust(2)
        await cq.message.answer("🌍 Select the country to move Frozen sessions to:", reply_markup=kb.as_markup())
        await cq.answer()
        
    elif action == "rm2fa":
        await cq.answer("Removing 2FA in background...")
        success = 0
        for path in res["healthy"]:
            phone = path.split("/")[-1].split("_")[0]
            s_data = next((x for x in db_sessions if x["number"] == phone), None)
            curr_pass = s_data.get("password") if s_data and s_data.get("password") != "None" else None
            
            client = TelegramClient(path, int(os.getenv("API_ID")), os.getenv("API_HASH"))
            try:
                await client.connect()
                await client.edit_2fa(current_password=curr_pass, new_password=None)
                with open(f"{path}.session", "rb") as f:
                    numbers_col.update_one({"number": phone}, {"$set": {"password": "None", "session_file": Binary(f.read())}})
                success += 1
            except Exception:
                pass
            finally:
                await client.disconnect()
        
        # Send as new message
        await cq.message.answer(f"✅ <b>2FA Removed!</b>\nRemoved from {success} healthy accounts in {country}.", parse_mode="HTML")
        
    elif action == "ch2fa":
        await cq.message.answer("⌨️ Send the NEW 2FA password to set for healthy accounts:")
        await state.set_state(CheckSessionsAdmin.waiting_new_2fa)
        await cq.answer()

# ================= 4. Follow-up Actions =================
@dp.message(StateFilter(CheckSessionsAdmin.waiting_new_2fa))
async def chk_change_2fa(msg: Message, state: FSMContext):
    new_pass = msg.text.strip()
    data = await state.get_data()
    res = data.get("check_results")
    country = data.get("check_country")
    db_sessions = data.get("check_sessions")
    
    success = 0
    for path in res["healthy"]:
        phone = path.split("/")[-1].split("_")[0]
        s_data = next((x for x in db_sessions if x["number"] == phone), None)
        curr_pass = s_data.get("password") if s_data and s_data.get("password") != "None" else None
        
        client = TelegramClient(path, int(os.getenv("API_ID")), os.getenv("API_HASH"))
        try:
            await client.connect()
            await client.edit_2fa(current_password=curr_pass, new_password=new_pass)
            with open(f"{path}.session", "rb") as f:
                numbers_col.update_one({"number": phone}, {"$set": {"password": new_pass, "session_file": Binary(f.read())}})
            success += 1
        except Exception:
            pass
        finally:
            await client.disconnect()
            if os.path.exists(f"{path}.session"):
                os.remove(f"{path}.session") # cleanup
    
    # Send as new message
    await msg.answer(f"✅ <b>2FA Changed!</b>\nUpdated to <code>{new_pass}</code> for {success} healthy accounts in {country}.", parse_mode="HTML")
    await state.clear()




@dp.callback_query(F.data.startswith("chk_freeze_to:"))
async def chk_freeze_to_country(cq: CallbackQuery, state: FSMContext):
    new_country = cq.data.split(":")[1]
    data = await state.get_data()
    res = data.get("check_results")
    old_country = data.get("check_country")
    
    moved = 0
    for path in res["frozen"]:
        phone = path.split("/")[-1].split("_")[0]
        numbers_col.update_one({"number": phone}, {"$set": {"country": new_country, "status": "frozen"}})
        moved += 1
        
    recount_stock(old_country)
    recount_stock(new_country)
    
    # Send as new message
    await cq.message.answer(f"✅ <b>Frozen accounts moved!</b>\n{moved} sessions sent from {old_country} to {new_country}.", parse_mode="HTML")
    await cq.answer()

# ================= Admin: Top Users Command =================

@dp.message(Command("topusers"))
async def cmd_top_users(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    
    # Parse page number from command (e.g., /topusers 2)
    args = msg.text.split()
    page = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1
    limit = 10
    skip = (page - 1) * limit

    # Aggregation to find top spenders
    pipeline = [
        {
            "$group": {
                "_id": "$user_id",
                "total_spend": {"$sum": "$price"}
            }
        },
        {"$sort": {"total_spend": -1}},
        {"$skip": skip},
        {"$limit": limit},
        {
            "$lookup": {
                "from": "users",
                "localField": "_id",
                "foreignField": "_id",
                "as": "user_info"
            }
        }
    ]

    top_spenders = list(orders_col.aggregate(pipeline))

    if not top_spenders:
        return await msg.answer("❌ No spending data found or page out of range.")

    response_text = f"🏆 <b>Top Spending Users (Page {page})</b>\n"
    response_text += "--------------------------------\n"

    for entry in top_spenders:
        user_id = entry["_id"]
        total_spend = entry["total_spend"]
        
        # Get username if available, else use ID
        user_data = entry["user_info"][0] if entry["user_info"] else {}
        username = user_data.get("username")
        name = f"@{username}" if username else f"ID: <code>{user_id}</code>"
        
        response_text += f"👤 {name}\n💰 Total spend: ₹{total_spend:.2f}\n"
        response_text += "---------\n"

    # Add navigation tip
    response_text += f"\n<i>Use <code>/topusers {page + 1}</code> for next page.</i>"
    
    await msg.answer(response_text, parse_mode="HTML")
    

@dp.message(Command("gban"))
async def cmd_gban(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    
    args = msg.text.split()
    target_id = await get_target_id(msg, args)
    
    if not target_id:
        return await msg.answer("⚠️ <b>Usage:</b>\n• Reply to a user with <code>/gban</code>\n• <code>/gban 12345678</code>\n• <code>/gban @username</code> (User must be in DB)", parse_mode="HTML")

    # Update or Create the user with banned status
    users_col.update_one(
        {"_id": target_id},
        {"$set": {"banned": True}},
        upsert=True # This ensures they are added to DB even if they never started the bot
    )
    
    await msg.answer(f"⛔ User <code>{target_id}</code> has been <b>BANNED</b> from the bot.", parse_mode="HTML")
    
    # Try to notify the user
    try:
        await bot.send_message(target_id, "🚫 <b>You have been banned from using this bot by the admin.</b>", parse_mode="HTML")
    except:
        pass

@dp.message(Command("ungban"))
async def cmd_ungban(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    
    args = msg.text.split()
    target_id = await get_target_id(msg, args)
    
    if not target_id:
        return await msg.answer("⚠️ <b>Usage:</b> Reply with <code>/ungban</code> or use ID/Username.")

    result = users_col.update_one({"_id": target_id}, {"$set": {"banned": False}})
    
    if result.matched_count > 0:
        await msg.answer(f"✅ User <code>{target_id}</code> has been <b>UNBANNED</b>.", parse_mode="HTML")
    else:
        await msg.answer("❌ User not found in database.")
        
        
# ================= Admin Broadcast (Forward Version - Aiogram Fix) =================
@dp.message(Command("broadcast"))
async def cmd_broadcast(msg: Message):
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ Not authorized.")

    if not msg.reply_to_message:
        return await msg.answer("⚠️ Reply to the message you want to broadcast with /broadcast.")

    broadcast_msg = msg.reply_to_message
    users = list(users_col.find({}))

    if not users:
        return await msg.answer("⚠️ No users found to broadcast.")

    sent_count = 0
    failed_count = 0

    for user in users:
        user_id = user["_id"]
        try:
            await bot.forward_message(
                chat_id=user_id,
                from_chat_id=broadcast_msg.chat.id,
                message_id=broadcast_msg.message_id
            )
            sent_count += 1
        except Exception as e:
            failed_count += 1
            print(f"Failed to send to {user_id}: {e}")

    await msg.answer(f"✅ Broadcast completed!\n\nSent: {sent_count}\nFailed: {failed_count}")
    



# ===== Register External Handlers =====
register_recharge_handlers(
    dp=dp, 
    bot=bot, 
    users_col=users_col, 
    txns_col=db["transactions"], 
    crypto_col=crypto_col, 
    settings_col=db["bot_settings"]  # <-- Add this new collection
)
register_server2_handlers(
    dp=dp, 
    bot=bot, 
    users_col=users_col, 
    orders_col=orders_col,
    get_or_create_user=get_or_create_user,
    is_admin_func=is_admin,
    ADMIN_IDS=ADMIN_IDS
)
register_server3_handlers(
    dp=dp,
    bot=bot,
    db=db,
    users_col=users_col,
    orders_col=orders_col,
    is_admin_func=is_admin,
    fmt_curr_func=fmt_curr
)
register_server4_handlers(
    dp=dp,
    bot=bot,
    db=db,
    users_col=users_col,
    orders_col=orders_col,
    settings_col=settings_col,
    admin_ids=ADMIN_IDS,
    ADMINLOG=ADMINLOG,
    SALES=SALES,
    TEMPORASMS_API_KEY=TEMPORASMS_API_KEY,
    BOTUSER=BOTUSER,
    CHANNEL=CHANNEL,
    exchange_rate=float(exchange_rate)
)


    
# ---- Add the new marketplace handler here ----
register_buysrc_panels_handlers(
    dp=dp,
    bot=bot,
    db=db,
    users_col=users_col,
    is_admin_func=is_admin,
    fmt_curr_func=fmt_curr
)


# Pass your dispatcher and DB instance to the new file
register_smmpanel_handlers(dp, db)


    
# =========================================================================
# 🚀 1. HIGH-PRIORITY ROUTING TRIGGERS (SERVER 3 ONLY)
# =========================================================================
# FIX: Added StateFilter(None) so it doesn't hijack FSM inputs, and icontains to strictly filter.
@dp.message(StateFilter(None), F.text.icontains("number change"))
async def handle_number_change_routing_triggers(msg: Message, state: FSMContext):
    text_lower = msg.text.lower().strip()
    
    # Edge Case Handler: Specific "telegram usa number change"
    if "telegram" in text_lower and "usa" in text_lower:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Go to Server 3 (USA Telegram)", callback_data="s3_tg_usa")]
        ])
        return await msg.answer("⚡ <b>Redirecting you to Server 3 Telegram USA Number Change Page:</b>", reply_markup=kb)

    # App-Specific Variations
    elif "telegram" in text_lower:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Go to Server 3 Telegram Menu", callback_data="s3_menu_telegram")]
        ])
        return await msg.answer("🍷 <b>Server 3 Telegram Number Change Panel:</b>", reply_markup=kb)
        
    elif "whatsapp" in text_lower:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Go to Server 3 WhatsApp Menu", callback_data="s3_menu_whatsapp")]
        ])
        return await msg.answer("💬 <b>Server 3 WhatsApp Number Change Panel:</b>", reply_markup=kb)

    # Catch-all base fallback trigger
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Go to Server 3 Land Page", callback_data="back_main")] 
        ])
        return await msg.answer("⏱️ <b>Redirecting you to Server 3 Landing Page:</b>", reply_markup=kb)


# =========================================================================
# 🔍 2. DYNAMIC LOOKUP SEARCH ENGINE (ANTI-HIJACK LOGIC)
# =========================================================================
# FIX: Added StateFilter(None) so users can send SMM links without interruption.
@dp.message(StateFilter(None), F.text & ~F.text.startswith("/"))
async def global_search_engine_handler(msg: Message, state: FSMContext):
    cleaned_text = msg.text.lower().strip()
    
    # Isolate country target term from application utility descriptions
    country_query = cleaned_text.replace("telegram", "").replace("whatsapp", "").replace("number change", "").replace("change", "").strip()
    
    if not country_query:
        return

    # 1. Server 1 - Strict full-word boundary regex mapping to prevent mismatched country names
    s1_country = countries_col.find_one({"name": {"$regex": f"^{re.escape(country_query)}$", "$options": "i"}})
    s1_stock = s1_country.get("stock_healthy", 0) if s1_country else 0
    s1_link_id = str(s1_country["_id"]) if s1_country else "main"

    # 2. Server 2 - Dynamic live import check
    s2_country_code = None
    s2_stock = 0
    s2_country_name = None
    try:
        s2_data = await get_available_countries()
        if s2_data and "countries" in s2_data:
            for code, info in s2_data["countries"].items():
                c_name = info.get("name", "").lower()
                # Strict exact full validation check to fix accidental India responses
                if country_query == c_name:
                    s2_country_code = code
                    s2_country_name = info.get("name")
                    s2_stock = info.get("qty", 0)
                    break
    except Exception:
        pass

    # 3. Server 3 Setup (Placeholder or Provider Status Verification)
    s3_stock = "Available"

    # Match execution context UI rendering layout format
    if s1_country or s2_country_code:
        display_title = s1_country["name"] if s1_country else s2_country_name
        
        response_text = (
            f"<b>Stock found for country:</b> <code>{display_title}</code>\n"
            f"<blockquote expandable>"
            f"Server 1 - {s1_stock} stock\n"
            f"Server 2 - {s2_stock} stock\n"
            f"Server 3 - {s3_stock} stock"
            f"</blockquote>"
        )
        
        # Style buttons with success layout configurations
        kb = InlineKeyboardBuilder()
        if s1_country:
            kb.button(text="🛒 Buy Server 1", callback_data=f"buy_s1_{s1_link_id}")
        if s2_country_code:
            kb.button(text="🛒 Buy Server 2", callback_data=f"s2:country:{s2_country_code}")
        kb.button(text="🛒 Buy Server 3", callback_data="buy_s3_main")
        kb.adjust(1)
        
        await msg.answer(response_text, reply_markup=kb.as_markup(), parse_mode="HTML")
        

# ================= Group Keyword & Stock Scanner =================
# Keyword mapping for easy detection
APP_KEYWORDS = {
    "tg": ["telegram", "tg", "tele", "t.me"],
    "wa": ["whatsapp", "wa", "ws", "wapp", "whatsup"]
}

COUNTRY_KEYWORDS = {
    "usa": ["usa", "united states", "+1", "us", "america"],
    "india": ["india", "+91", "in", "indian"],
    "uk": ["uk", "united kingdom", "+44", "england", "britain"],
    "indonesia": ["indonesia", "+62", "indo", "id"],
    "canada": ["canada", "+1 canada", "ca"],
    "nigeria": ["nigeria", "+234", "ng"],
    "brazil": ["brazil", "+55", "br"],
    "russia": ["russia", "+7", "ru"],
    "philippines": ["philippines", "+63", "ph"],
    "sierra leone": ["sierra leone", "+232", "sl"],
    "vietnam": ["vietnam", "+84", "vn"],
    "pakistan": ["pakistan", "+92", "pk"]
}

@dp.message(F.chat.id == -1003261310536)
async def group_stock_scanner(msg: Message):
    if not msg.text:
        return
        
    text = msg.text.lower()
    
    # 1. Detect Application
    target_app = None
    for app_code, keywords in APP_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            target_app = app_code
            break
            
    if not target_app:
        return # Do not trigger if app isn't mentioned

    # 2. Detect Country
    target_country_key = None
    for country_key, keywords in COUNTRY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            target_country_key = country_key
            break
            
    if not target_country_key:
        return # Do not trigger if country isn't mentioned

    bot_username = (await bot.get_me()).username
    available_buttons = []
    app_display_name = "Telegram" if target_app == "tg" else "WhatsApp"
    display_country_name = target_country_key.title()

    # --- CHECK SERVER 1 (Only Telegram) ---
    if target_app == "tg":
        # Check MongoDB countries collection
        s1_country = countries_col.find_one({"name": {"$regex": f"^{target_country_key}$", "$options": "i"}})
        if s1_country and s1_country.get("stock", 0) > 0:
            price = s1_country.get("price_healthy", 0)
            clean_country = s1_country["name"].replace(" ", "_")
            deep_link = f"https://t.me/{bot_username}?start=buy_s1_{clean_country}"
            available_buttons.append([InlineKeyboardButton(
                text=f"{s1_country['name']} | Server 1 | {fmt_curr(price)}",
                url=deep_link
            )])
            display_country_name = s1_country['name']

    # --- CHECK SERVER 2 (Only Telegram) ---
    if target_app == "tg":
        try:
            from server2_api import get_available_countries, get_final_price, format_price_inr
            s2_data = await get_available_countries()
            if s2_data and "countries" in s2_data:
                for code, info in s2_data["countries"].items():
                    name = info.get("name", "").lower()
                    if (target_country_key == code.lower() or target_country_key in name) and info.get("qty", 0) > 0:
                        _, _, _, final_inr = await get_final_price(code, info.get("price", "0"))
                        deep_link = f"https://t.me/{bot_username}?start=buy_s2_{code}"
                        available_buttons.append([InlineKeyboardButton(
                            text=f"{info.get('name', code)} | Server 2 | {format_price_inr(final_inr)}",
                            url=deep_link
                        )])
                        display_country_name = info.get('name', display_country_name)
                        break
        except Exception as e:
            print(f"Group Scanner Server 2 Error: {e}")

    # --- CHECK SERVER 3 (Telegram & WhatsApp) ---
    try:
        import provider
        s3_offers = provider.get_active_offers(target_app)
        for offer in s3_offers:
            if target_country_key in offer["country"].lower():
                clean_country = offer["country"].replace(" ", "_")
                deep_link = f"https://t.me/{bot_username}?start=buy_s3_{target_app}_{clean_country}"
                available_buttons.append([InlineKeyboardButton(
                    text=f"{offer['country']} | Server 3 | {fmt_curr(offer['bot_price'])}",
                    url=deep_link
                )])
                display_country_name = offer["country"]
                break # Only show the lowest/first operator for brevity
    except Exception as e:
        print(f"Group Scanner Server 3 Error: {e}")

    # If stock exists anywhere, send the message and schedule auto-deletion
    if available_buttons:
        reply_text = (
            f"✅ <b>{display_country_name} {app_display_name} Found!</b>\n"
            f"⚡ Tap a button below to purchase instantly from @{bot_username}:"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=available_buttons)
        sent_msg = await msg.reply(reply_text, parse_mode="HTML", reply_markup=kb)
        
        # Schedule auto-delete after 5 minutes (300 seconds)
        async def delete_after_delay(message_to_delete):
            await asyncio.sleep(300)
            try:
                await message_to_delete.delete()
            except Exception:
                pass
        asyncio.create_task(delete_after_delay(sent_msg))

    
    
# ===== Bot Runner =====
async def main():
    print("Bot started.")
    asyncio.create_task(update_usdt_rate_task()) # <--- Starts the live rate updater
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    
if __name__ == "__main__":
    asyncio.run(main())
    
