import os
import asyncio
import html
from datetime import datetime, timezone
from typing import Dict, Optional

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardButton, 
    InlineKeyboardMarkup, CopyTextButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command, StateFilter

# Import from server2_api
from server2_api import (
    get_available_countries, get_country_info, buy_number, get_code,
    get_usd_to_inr_rate, convert_price_to_inr, format_price_inr,
    get_final_price, set_profit_percent, get_profit_percent,
    set_country_price, set_country_profit, remove_country_override,
    get_country_price_settings, get_all_price_settings, bulk_update_profit,
    get_balance as get_panel_balance
)
# ================= Anti-Double Click Protection =================
_click_freeze = {}
FREEZE_SECONDS = 5

async def is_frozen(user_id: int, action: str = "default") -> bool:
    """Check if user action is frozen to prevent double-clicks"""
    key = f"{user_id}:{action}"
    now = datetime.now(timezone.utc).timestamp()
    
    if key in _click_freeze:
        if now - _click_freeze[key] < FREEZE_SECONDS:
            return True
    
    _click_freeze[key] = now
    return False


def clear_freeze(user_id: int, action: str = "default"):
    """Manually clear freeze (optional)"""
    key = f"{user_id}:{action}"
    _click_freeze.pop(key, None)


# ================= FSM States =================
class Server2Buy(StatesGroup):
    waiting_country = State()
    waiting_confirm = State()
    waiting_search = State()

class Server2Admin(StatesGroup):
    waiting_profit_percent = State()
    waiting_custom_price = State()
    waiting_bulk_profit = State()
    waiting_manual_price = State()
    waiting_manual_country_select = State()


# ================= Configuration =================
SALESLOG = "-1003349993686"
ADMINLOG = "-1003208353049"
COUNTRIES_PER_PAGE = 24  # 24 countries per page
COUNTRIES_PER_ROW = 2    # 2 countries per row

# Callback data prefix
S2_PREFIX = "s2"


# ================= Helper: Build Country Menu =================

async def build_country_menu(page: int = 0, for_admin: bool = False, search_query: str = None) -> tuple:
    """
    Build paginated country keyboard
    Returns: (text, reply_markup, total_pages)
    """
    data = await get_available_countries()
    
    if not data or "countries" not in data:
        return "❌ <b>Server 2 is temporarily unavailable.</b>\n<i>Please try again later or use Server 1.</i>", None, 0
    
    countries = data["countries"]
    country_list = []
    
    for code, info in countries.items():
        country_list.append({
            "code": code,
            "name": info.get("name", code),
            "qty": info.get("qty", 0),
            "price_usd": info.get("price", "0")
        })
    
    total = len(country_list)
    if total == 0:
        return "❌ <b>No countries available on Server 2.</b>", None, 0
    
    # Filter by search if provided
    if search_query:
        search_lower = search_query.lower().strip()
        filtered = []
        for c in country_list:
            if (search_lower in c["code"].lower() or 
                search_lower in c["name"].lower() or
                search_lower in c.get("flag", "").lower()):
                filtered.append(c)
        country_list = filtered
        total = len(country_list)
        if total == 0:
            return f"❌ <b>No countries found for:</b> <code>{html.escape(search_query)}</code>", None, 0
    
    total_pages = (total - 1) // COUNTRIES_PER_PAGE + 1
    page = max(0, min(page, total_pages - 1))
    
    start = page * COUNTRIES_PER_PAGE
    end = start + COUNTRIES_PER_PAGE
    paginated = country_list[start:end]
    
    kb = InlineKeyboardBuilder()
    
    for c in paginated:
        # Calculate INR price
        _, _, _, final_inr = await get_final_price(c["code"], c["price_usd"])
        price_str = format_price_inr(final_inr)
        stock_str = f"({c['qty']})" if c["qty"] > 0 else "❌"
        
        btn_text = f"{c['name']}|{price_str}"
        
        if for_admin:
            kb.button(text=btn_text[:64], callback_data=f"{S2_PREFIX}:admin_edit:{c['code']}")
        else:
            kb.button(text=btn_text[:64], callback_data=f"{S2_PREFIX}:country:{c['code']}")
    
    kb.adjust(COUNTRIES_PER_ROW)  # 2 per row
    
    # Page number buttons
    if total_pages > 1:
        page_buttons = []
        for p in range(total_pages):
            if p == page:
                page_buttons.append(InlineKeyboardButton(
                    text=f"[{p + 1}]",
                    callback_data=f"{S2_PREFIX}:page:{p}"
                ))
            else:
                page_buttons.append(InlineKeyboardButton(
                    text=str(p + 1),
                    callback_data=f"{S2_PREFIX}:page:{p}"
                ))
        
        # Add page buttons in rows of 8
        for i in range(0, len(page_buttons), 8):
            kb.row(*page_buttons[i:i+8])
    
    # Search button
    kb.row(InlineKeyboardButton(text="Search", callback_data=f"{S2_PREFIX}:search", icon_custom_emoji_id="5429571366384842791", style="success"))
    
    # Home button
    kb.row(InlineKeyboardButton(text="Home", callback_data="back_main", icon_custom_emoji_id="5409284148491726576", style="danger"))
    
    # Build text
    rate = await get_usd_to_inr_rate()
    profit = get_profit_percent()
    
    if search_query:
        text = (
            f"<b>🔍 Search Results for:</b> <code>{html.escape(search_query)}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>📄 Page:</b> {page + 1}/{total_pages}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Select a country to purchase:</i>"
        )
    else:
        text = (
            f"<b>🚀 Server 2 — tgbitz Panel</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>📄 Page:</b> {page + 1}/{total_pages}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Select a country to purchase:</i>"
        )
    
    return text, kb.as_markup(), total_pages


# ================= Handler: Server 2 Entry =================

async def callback_buy_server2(cq: CallbackQuery, state: FSMContext, users_col, get_or_create_user):
    """Main entry point for Server 2 — called from bot.py"""
    
    if await is_frozen(cq.from_user.id, "server2_menu"):
        return await cq.answer("⏳ Please wait 5 seconds...", show_alert=True)
    
    await cq.answer("🚀 Loading Server 2...")
    
    user = get_or_create_user(cq.from_user.id, cq.from_user.username)
    balance = user.get("balance", 0.0)
    
    text, kb, _ = await build_country_menu(page=0)
    
    # Prepend balance info
    text = f"💰 <b>Your Balance:</b> ₹{balance:.2f}\n{text}"
    
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb, disable_web_page_preview=True)


# ================= Handler: Country Pagination =================

async def callback_s2_paginate(cq: CallbackQuery, state: FSMContext, users_col, get_or_create_user):
    """Handle page navigation"""
    
    if await is_frozen(cq.from_user.id, f"page_{cq.data}"):
        return await cq.answer("⏳ Please wait...", show_alert=True)
    
    _, _, page_str = cq.data.split(":")
    try:
        page = int(page_str)
    except ValueError:
        page = 0
    
    await cq.answer(f"📄 Page {page + 1}")
    
    user = get_or_create_user(cq.from_user.id, cq.from_user.username)
    balance = user.get("balance", 0.0)
    
    text, kb, _ = await build_country_menu(page=page)
    text = f"💰 <b>Your Balance:</b> ₹{balance:.2f}\n{text}"
    
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb, disable_web_page_preview=True)


# ================= Handler: Search =================

async def callback_s2_search(cq: CallbackQuery, state: FSMContext):
    """Start search flow"""
    
    if await is_frozen(cq.from_user.id, "search_start"):
        return await cq.answer("⏳ Please wait...", show_alert=True)
    
    await cq.answer("🔍 Enter search query...")
    
    text = (
        f"<b>🔍 Search Countries</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Send country code (e.g. <code>US</code>, <code>IN</code>) or country name/flag.</i>\n"
        f"<i>Example: <code>🇮🇳</code> or <code>India</code> or <code>IN</code></i>"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Back", callback_data=f"{S2_PREFIX}:page:0", icon_custom_emoji_id="5409284148491726576", style="danger")]
    ])
    
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await state.set_state(Server2Buy.waiting_search)


async def handle_s2_search(msg: Message, state: FSMContext, users_col, get_or_create_user, orders_col, bot):
    """Handle search query and show results"""
    
    if await is_frozen(msg.from_user.id, "search_process"):
        return await msg.answer("⏳ Please wait 5 seconds...")
    
    search_query = msg.text.strip()
    
    if not search_query:
        return await msg.answer("❌ Please enter a valid search query.")
    
    user = get_or_create_user(msg.from_user.id, msg.from_user.username)
    balance = user.get("balance", 0.0)
    
    # Search for country
    data = await get_available_countries()
    
    if not data or "countries" not in data:
        return await msg.answer("❌ Server 2 is temporarily unavailable.")
    
    countries = data["countries"]
    search_lower = search_query.lower()
    
    matched = None
    for code, info in countries.items():
        name = info.get("name", "").lower()
        if (search_lower == code.lower() or 
            search_lower in name or
            search_lower in info.get("flag", "").lower()):
            matched = {"code": code, **info}
            break
    
    if not matched:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Search Again", callback_data=f"{S2_PREFIX}:search", icon_custom_emoji_id="5429571366384842791", style="success")],
            [InlineKeyboardButton(text="Back to List", callback_data=f"{S2_PREFIX}:page:0", icon_custom_emoji_id="5409284148491726576", style="danger")]
        ])
        return await msg.answer(
            f"❌ <b>No country found for:</b> <code>{html.escape(search_query)}</code>\n\n"
            f"<i>Try searching with country code (e.g. US, IN) or name.</i>",
            parse_mode="HTML",
            reply_markup=kb
        )
    
    # Show matched country with buy option
    country_code = matched["code"]
    country = matched
    
    panel_usd, inr_base, profit_pct, final_inr = await get_final_price(country_code, country.get("price", "0"))
    qty = country.get("qty", 0)
    
    text = (
        f"<b>🚀 Server 2 — Account Purchase</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<blockquote><b>🌍 Country:</b> {html.escape(country.get('name', country_code))}\n"
        f"<b>📊 Stock:</b> {qty} accounts\n"
        f"<b>🏷️ Price:</b> {format_price_inr(final_inr)}</blockquote>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Your Balance:</b> ₹{balance:.2f}\n"
    )
    
    kb_buttons = []
    
    if balance < final_inr:
        text += f"\n❌ <b>Insufficient Balance!</b>\n<i>Shortage: ₹{final_inr - balance:.2f}</i>"
        kb_buttons.append([InlineKeyboardButton(text="💎 Recharge", callback_data="recharge")])
    elif qty < 1:
        text += "\n⚠️ <b>Out of Stock!</b>"
    else:
        text += "\n✅ <b>Ready to purchase?</b>"
        kb_buttons.append([InlineKeyboardButton(
            text=f"🛒 Buy for {format_price_inr(final_inr)}", 
            callback_data=f"{S2_PREFIX}:confirm:{country_code}:{final_inr:.2f}"
        )])
    
    kb_buttons.append([InlineKeyboardButton(text="Search Again", callback_data=f"{S2_PREFIX}:search", icon_custom_emoji_id="5429571366384842791", style="success")])
    kb_buttons.append([InlineKeyboardButton(text="Back to List", callback_data=f"{S2_PREFIX}:page:0", icon_custom_emoji_id="5409284148491726576", style="danger")])
    kb_buttons.append([InlineKeyboardButton(text="Home", callback_data="back_main")])
    
    await msg.answer(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_buttons))
    await state.clear()


# ================= Handler: Country Selection =================

async def callback_s2_country(cq: CallbackQuery, state: FSMContext, users_col, get_or_create_user, orders_col, bot):
    """Show country details and buy option"""
    
    if await is_frozen(cq.from_user.id, "country_select"):
        return await cq.answer("⏳ Please wait...", show_alert=True)
    
    _, _, country_code = cq.data.split(":", 2)
    
    await cq.answer("🔄 Fetching details...")
    
    # Get fresh country info
    data = await get_available_countries()
    if not data or country_code not in data.get("countries", {}):
        return await cq.answer("❌ Country no longer available", show_alert=True)
    
    country = data["countries"][country_code]
    user = get_or_create_user(cq.from_user.id, cq.from_user.username)
    balance = user.get("balance", 0.0)
    
    panel_usd, inr_base, profit_pct, final_inr = await get_final_price(country_code, country.get("price", "0"))
    
    qty = country.get("qty", 0)
    
    text = (
        f"<b>🚀 Server 2 — Account Purchase</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<blockquote><b>🌍 Country:</b> {html.escape(country.get('name', country_code))}\n"
        f"<b>📊 Stock:</b> {qty} accounts\n"
        f"<b>🏷️ Price:</b> {format_price_inr(final_inr)}</blockquote>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Your Balance:</b> ₹{balance:.2f}\n"
    )
    
    if balance < final_inr:
        text += f"\n❌ <b>Insufficient Balance!</b>\n<i>Shortage: ₹{final_inr - balance:.2f}</i>"
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="Recharge •", callback_data="recharge"))
        kb.row(InlineKeyboardButton(text="Back •", callback_data=f"{S2_PREFIX}:page:0", icon_custom_emoji_id="5409284148491726576", style="danger"))
        kb.row(InlineKeyboardButton(text="Home •", callback_data="back_main"))
    elif qty < 1:
        text += "\n⚠️ <b>Out of Stock!</b>"
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="Back •", callback_data=f"{S2_PREFIX}:page:0", icon_custom_emoji_id="5409284148491726576", style="danger"))
        kb.row(InlineKeyboardButton(text="Home •", callback_data="back_main"))
    else:
        text += "\n✅ <b>Ready to purchase?</b>"
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(
            text=f"🛒 Buy for {format_price_inr(final_inr)}", 
            callback_data=f"{S2_PREFIX}:confirm:{country_code}:{final_inr:.2f}"
        ))
        kb.row(InlineKeyboardButton(text="Back", callback_data=f"{S2_PREFIX}:page:0", icon_custom_emoji_id="5409284148491726576", style="danger"))
        kb.row(InlineKeyboardButton(text="Home", callback_data="back_main"))
    
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup(), disable_web_page_preview=True)


# ================= Handler: Confirm Purchase =================

async def callback_s2_confirm(cq: CallbackQuery, state: FSMContext, users_col, get_or_create_user, orders_col, bot, is_admin):
    """Execute purchase from Tgbitz panel"""
    
    if await is_frozen(cq.from_user.id, "s2_purchase"):
        return await cq.answer("⏳ Purchase processing... Please wait 5s", show_alert=True)
    
    parts = cq.data.split(":")
    country_code = parts[2]
    price_inr = float(parts[3])
    
    user_id = cq.from_user.id
    user = get_or_create_user(user_id, cq.from_user.username)
    balance = user.get("balance", 0.0)
    
    # Validation
    if balance < price_inr:
        await cq.answer("❌ Insufficient balance!", show_alert=True)
        return await callback_buy_server2(cq, state, users_col, get_or_create_user)
    
    # Show processing
    await cq.answer("🔄 Processing purchase...")
    processing_msg = await cq.message.edit_text(
        "<b>🔄 Processing Purchase...</b>\n"
        "<i>Contacting Tgbitz servers...</i>",
        parse_mode="HTML"
    )
    
    # Buy from panel
    result = await buy_number(country_code)
    
    if not result:
        await processing_msg.edit_text(
            "❌ <b>Purchase Failed</b>\n"
            "<i>Server 2 API error. Please try again or contact support.</i>\n\n"
            "<b>Your balance was NOT deducted.</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◾ Back", callback_data=f"{S2_PREFIX}:page:0")],
                [InlineKeyboardButton(text="◾ Home", callback_data="back_main")]
            ])
        )
        return
    
    # Extract data
    number = result.get("Number", "Unknown")
    panel_price_usd = result.get("price", "0")
    panel_new_balance = result.get("new_balance", "N/A")
    country_name = result.get("name", country_code)
    
    # Deduct balance
    new_balance = balance - price_inr
    users_col.update_one({"_id": user_id}, {"$set": {"balance": new_balance}})
    
    # Log order
    orders_col.insert_one({
        "user_id": user_id,
        "country": country_name,
        "number": number,
        "price": price_inr,
        "panel_price_usd": panel_price_usd,
        "server": 2,
        "status": "purchased",
        "created_at": datetime.now(timezone.utc)
    })
    
    # Build success message with OTP button
    text_to_copy = str(number)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📩 Get OTP",
                callback_data=f"{S2_PREFIX}:get_otp:{number}"
            ),
            InlineKeyboardButton(
                text="📋 Copy Number",
                copy_text=CopyTextButton(text=text_to_copy)
            )
        ],
        
    ])
    
    success_text = (
        f"<pre>✅ Purchased Successfully!</pre>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>🚀 Server:</b> 2\n"
        f"<b>🌍 Country:</b> {html.escape(country_name)}\n"
        f"<b>📞 Number:</b> <code>{number}</code>\n"
        f"<b>🏷️ Price:</b> {format_price_inr(price_inr)}\n"
        f"<b>💸 Balance:</b> ₹{new_balance:.2f}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Click 'Get OTP' to receive the login code.</i>"
    )
    
    await processing_msg.edit_text(success_text, parse_mode="HTML", reply_markup=kb)
    
    # ===== SALES LOG =====
    if not number.startswith("+"):
        display_number = f"+{number}"
    else:
        display_number = number
    masked_number = display_number[:6] + "•••••" if len(display_number) > 6 else display_number
    
    channel_message = (
        f"<pre><u>✅ <b>New Number Purchase Successful</b></u></pre>\n\n"
        f"➖ <b><u>Country:</u></b> {html.escape(country_name)}\n"
        f"➖ <b><u>Application:</u> Теlegг@м 🍷</b>\n\n"
        f"➕ <b>Number: {masked_number} 📞</b>\n"
        f"➕ <b>Server:</b> (2) 🚀\n"
        f"<b>• @Tgbitz || @Tgbitz_bot</b>"
    )
    
        # --- DYNAMIC DEEP LINK FOR SERVER 2 LOGS ---
    bot_me = await bot.get_me()
    buy_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"• Buy {country_name} Now •", 
            url=f"https://t.me/{bot_me.username}?start=buy_s2_{country_code}"
        )]
    ])

    try:
        await bot.send_message(SALESLOG, channel_message, parse_mode="HTML", reply_markup=buy_button)
    except Exception as e:
        print(f"[Server2] Sales log error: {e}")
    
    # ===== ADMIN LOG =====
    buyer_name = user.get("username") or f"User {user_id}"
    panel_usd, inr_base, profit_pct, _ = await get_final_price(country_code, panel_price_usd)
    
    admin_message = (
        f"<pre>📢 Server 2 Purchase Alert</pre>\n\n"
        f"<b>• Application:</b> Telegram\n"
        f"<b>• Country:</b> {html.escape(country_name)}\n"
        f"<b>• Number:</b> <code>{number}</code>\n"
        f"<b>• Server:</b> 2 (Tgbitz)\n\n"
        f"<b>💵 Panel Price:</b> ${panel_usd:.2f} USD\n"
        f"<b>💱 Base INR:</b> ₹{inr_base:.2f}\n"
        f"<b>📈 Profit %:</b> {profit_pct}%\\n"
        f"<b>💰 Sold For:</b> {format_price_inr(price_inr)}\n\n"
        f"<b>👤 User:</b> @{buyer_name} (<code>{user_id}</code>)\n"
        f"<b>💰 Balance:</b> ₹{new_balance:.2f}"
    )
    
    userbutton = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="USER ID", url=f"tg://openmessage?user_id={user_id}")]
    ])
    
    try:
        await bot.send_message(ADMINLOG, admin_message, parse_mode="HTML", reply_markup=userbutton)
    except Exception as e:
        print(f"[Server2] Admin log error: {e}")


# ================= Handler: Get OTP =================

async def callback_s2_get_otp(cq: CallbackQuery, state: FSMContext, bot):
    """Fetch OTP from panel"""
    
    if await is_frozen(cq.from_user.id, f"otp_{cq.data}"):
        return await cq.answer("⏳ OTP fetch in progress...", show_alert=True)
    
    parts = cq.data.split(":")
    number = parts[2] if len(parts) > 2 else ""
    
    await cq.answer("🔄 Fetching OTP...")
    
    status_msg = await cq.message.answer(f"🔍 <b>Fetching OTP for {number}...</b>")
    
    result = await get_code(number)
    
    if not result:
        await status_msg.edit_text(
            f"❌ <b>OTP Fetch Failed</b>\n"
            f"<i>No code received yet or session expired.</i>\n\n"
            f"<b>Number:</b> <code>{number}</code>\n"
            f"<i>Try again in a few seconds...</i>",
            parse_mode="HTML"
        )
        return
    
    code = result.get("code", "N/A")
    password = result.get("pass", "None")
    
    # Build response
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Copy OTP•",
                copy_text=CopyTextButton(text=str(code))
            ),
            InlineKeyboardButton(
                text="Copy Pass•",
                copy_text=CopyTextButton(text=str(password))
            )
        ],
        
    ])
    
    response_text = (
        f"<pre>Order Completed ✅</pre>\n"
        f"✅ <b>𝐍𝗨𝐌𝐁𝐄𝐑</b> - <code>{number}</code>\n"
        f"💬 <b>𝐂𝐎𝐃𝐄</b> - <code>{code}</code>\n"
        f"💬 <b>𝐏𝐀𝐒𝐒</b> - <code>{password}</code>\n"
        f"<i>🚀 Server - 2 </i>"
    )
    
    await status_msg.delete()
    await bot.send_message(
        chat_id=cq.message.chat.id,
        text=response_text,
        parse_mode="HTML",
        reply_markup=kb
    )


# ================= ADMIN COMMAND: /server2 =================

async def cmd_server2(msg: Message, state: FSMContext, is_admin_func):
    """Admin panel for Server 2 pricing"""
    
    if not is_admin_func(msg.from_user.id):
        return await msg.answer("❌ Not authorized.")
    
    rate = await get_usd_to_inr_rate()
    profit = get_profit_percent()
    balance = await get_panel_balance()
    
    # Get sales stats
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    
    # These would need to be passed or accessed differently - using placeholder logic
    # In actual implementation, you'd query orders_col for these stats
    
    text = (
        f"<b>🚀 Server 2 — Admin Panel</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>💱 Live Rate:</b> 1 USD = ₹{rate:.2f}\n"
        f"<b>📈 Global Profit:</b> +{profit}%\n"
    )
    
    if balance is not None:
        inr_value = balance * rate
        text += f"<b>💰 Panel Balance:</b> ${balance:.2f} (₹{inr_value:.2f})\n"
    else:
        text += f"<b>💰 Panel Balance:</b> ❌ Failed to fetch\\n"
    
    text += (
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Choose an option:</b>"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Bulk Update (%)", callback_data=f"{S2_PREFIX}:admin:bulk"),
            InlineKeyboardButton(text="✏️ Manual Edit", callback_data=f"{S2_PREFIX}:admin:manual")
        ],
        [
            InlineKeyboardButton(text="💰 Check Panel Balance", callback_data=f"{S2_PREFIX}:admin:balance")
        ],
        [
            InlineKeyboardButton(text="📋 View All Settings", callback_data=f"{S2_PREFIX}:admin:settings")
        ]
    ])
    
    await msg.answer(text, parse_mode="HTML", reply_markup=kb)


# ================= Admin: Bulk Update =================

async def callback_s2_admin_bulk(cq: CallbackQuery, state: FSMContext):
    """Start bulk profit update"""
    
    if await is_frozen(cq.from_user.id, "admin_action"):
        return await cq.answer("⏳ Please wait...", show_alert=True)
    
    await cq.answer()
    
    text = (
        f"<b>📊 Bulk Price Update</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Current global profit: <b>+{get_profit_percent()}%</b>\n\n"
        f"<i>Enter the new profit percentage to apply to ALL countries.</i>\n"
        f"<i>Example: <code>15</code> for 15% markup on panel price.</i>\n\n"
        f"<b>This will remove all individual country overrides.</b>"
    )
    
    await cq.message.edit_text(text, parse_mode="HTML")
    await state.set_state(Server2Admin.waiting_bulk_profit)


async def handle_bulk_profit(msg: Message, state: FSMContext):
    """Process bulk profit update"""
    
    try:
        percent = float(msg.text.strip())
        if percent < 0 or percent > 500:
            raise ValueError("Out of range")
    except ValueError:
        return await msg.answer("❌ Invalid percentage. Send a number between 0 and 500.")
    
    bulk_update_profit(percent)
    
    await msg.answer(
        f"✅ <b>Bulk Update Applied!</b>\n\n"
        f"<b>📈 New Global Profit:</b> +{percent}%\n"
        f"<b>🌍 All countries updated.</b>\n\n"
        f"<i>Individual overrides have been cleared.</i>",
        parse_mode="HTML"
    )
    await state.clear()


# ================= Admin: Manual Edit =================

async def callback_s2_admin_manual(cq: CallbackQuery, state: FSMContext):
    """Show countries for manual price editing"""
    
    if await is_frozen(cq.from_user.id, "admin_manual"):
        return await cq.answer("⏳ Please wait...", show_alert=True)
    
    await cq.answer("🔄 Loading countries...")
    
    text, kb, _ = await build_country_menu(page=0, for_admin=True)
    
    header = (
        f"<b>✏️ Manual Price Editor</b>\n"
        f"<i>Click any country to change its price.</i>\n\n"
    )
    
    await cq.message.edit_text(header + text, parse_mode="HTML", reply_markup=kb, disable_web_page_preview=True)


async def callback_s2_admin_edit_country(cq: CallbackQuery, state: FSMContext):
    """Show edit options for specific country"""
    
    parts = cq.data.split(":")
    country_code = parts[3] if len(parts) > 3 else ""
    
    await cq.answer()
    
    # Get current info
    data = await get_available_countries()
    country = data.get("countries", {}).get(country_code, {}) if data else {}
    country_name = country.get("name", country_code)
    panel_price = country.get("price", "0")
    
    panel_usd, inr_base, profit_pct, final_inr = await get_final_price(country_code, panel_price)
    settings = get_country_price_settings(country_code)
    
    text = (
        f"<b>✏️ Editing: {html.escape(country_name)}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>💵 Panel Price:</b> ${panel_usd:.2f} USD\n"
        f"<b>💱 Base INR:</b> ₹{inr_base:.2f}\n"
        f"<b>📈 Current Profit:</b> {profit_pct}%\n"
        f"<b>🏷️ Current Price:</b> {format_price_inr(final_inr)}\n\n"
    )
    
    if settings.get("override"):
        text += f"<b>⚠️ Custom Price:</b> ₹{settings['custom_inr']:.2f}\n"
    
    text += (
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Choose action:</b>"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💰 Set Custom INR Price", 
                callback_data=f"{S2_PREFIX}:admin:setprice:{country_code}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📈 Set Individual Profit %", 
                callback_data=f"{S2_PREFIX}:admin:setprofit:{country_code}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🗑️ Reset to Global", 
                callback_data=f"{S2_PREFIX}:admin:reset:{country_code}"
            )
        ],
        [
            InlineKeyboardButton(text="◀️ Back to List", callback_data=f"{S2_PREFIX}:admin:manual")
        ]
    ])
    
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb)


async def callback_s2_admin_set_price(cq: CallbackQuery, state: FSMContext):
    """Start custom price setting"""
    
    parts = cq.data.split(":")
    country_code = parts[3] if len(parts) > 3 else ""
    
    await cq.answer()
    
    data = await get_available_countries()
    country = data.get("countries", {}).get(country_code, {}) if data else {}
    country_name = country.get("name", country_code)
    
    await state.update_data(edit_country_code=country_code)
    
    text = (
        f"<b>💰 Set Custom Price for {html.escape(country_name)}</b>\n\n"
        f"<i>Enter the exact INR price you want to sell this country for.</i>\n"
        f"<i>Example: <code>45</code> or <code>120.50</code></i>\n\n"
        f"<b>This will override the automatic profit calculation.</b>"
    )
    
    await cq.message.edit_text(text, parse_mode="HTML")
    await state.set_state(Server2Admin.waiting_custom_price)


async def handle_custom_price(msg: Message, state: FSMContext):
    """Process custom price input"""
    
    data = await state.get_data()
    country_code = data.get("edit_country_code")
    
    if not country_code:
        await state.clear()
        return await msg.answer("❌ Session expired. Use /server2 again.")
    
    try:
        price = float(msg.text.strip())
        if price < 1:
            raise ValueError("Too low")
    except ValueError:
        return await msg.answer("❌ Invalid price. Send a number ≥ 1.")
    
    set_country_price(country_code, price)
    
    await msg.answer(
        f"✅ <b>Custom Price Set!</b>\n\n"
        f"<b>🌍 Country:</b> {country_code}\n"
        f"<b>💰 New Price:</b> ₹{price:.2f}\n\n"
        f"<i>This country now uses a fixed price instead of profit %.</i>",
        parse_mode="HTML"
    )
    await state.clear()


async def callback_s2_admin_set_profit(cq: CallbackQuery, state: FSMContext):
    """Start individual profit setting"""
    
    parts = cq.data.split(":")
    country_code = parts[3] if len(parts) > 3 else ""
    
    await cq.answer()
    
    data = await get_available_countries()
    country = data.get("countries", {}).get(country_code, {}) if data else {}
    country_name = country.get("name", country_code)
    
    await state.update_data(edit_country_code=country_code, edit_type="profit")
    
    current = get_country_price_settings(country_code).get("profit_percent", get_profit_percent())
    
    text = (
        f"<b>📈 Set Profit % for {html.escape(country_name)}</b>\n\n"
        f"<b>Current:</b> {current}%\n"
        f"<i>Enter new profit percentage for this country only.</i>\n"
        f"<i>Example: <code>20</code> for 20% markup.</i>"
    )
    
    await cq.message.edit_text(text, parse_mode="HTML")
    await state.set_state(Server2Admin.waiting_manual_price)


async def handle_manual_price(msg: Message, state: FSMContext):
    """Process manual price/profit input"""
    
    data = await state.get_data()
    country_code = data.get("edit_country_code")
    edit_type = data.get("edit_type", "price")
    
    if not country_code:
        await state.clear()
        return await msg.answer("❌ Session expired. Use /server2 again.")
    
    try:
        value = float(msg.text.strip())
        if value < 0 or value > 500:
            raise ValueError("Out of range")
    except ValueError:
        return await msg.answer("❌ Invalid value. Send a number between 0 and 500.")
    
    if edit_type == "profit":
        set_country_profit(country_code, value)
        await msg.answer(
            f"✅ <b>Profit Updated!</b>\n\n"
            f"<b>🌍 Country:</b> {country_code}\n"
            f"<b>📈 New Profit:</b> {value}%\n"
            f"<i>Other countries remain unchanged.</i>",
            parse_mode="HTML"
        )
    else:
        set_country_price(country_code, value)
        await msg.answer(
            f"✅ <b>Price Updated!</b>\n\n"
            f"<b>🌍 Country:</b> {country_code}\n"
            f"<b>💰 New Price:</b> ₹{value:.2f}",
            parse_mode="HTML"
        )
    
    await state.clear()


async def callback_s2_admin_reset(cq: CallbackQuery, state: FSMContext):
    """Reset country to global settings"""
    
    parts = cq.data.split(":")
    country_code = parts[3] if len(parts) > 3 else ""
    
    await cq.answer()
    
    remove_country_override(country_code)
    
    await cq.message.edit_text(
        f"✅ <b>Reset Complete!</b>\n\n"
        f"<b>🌍 Country:</b> {country_code}\n"
        f"<i>Reverted to global profit settings.</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Back to List", callback_data=f"{S2_PREFIX}:admin:manual")]
        ])
    )


# ================= Admin: Panel Balance =================

async def callback_s2_admin_balance(cq: CallbackQuery, state: FSMContext):
    """Check Tgbitz panel balance"""
    
    if await is_frozen(cq.from_user.id, "admin_balance"):
        return await cq.answer("⏳ Please wait...", show_alert=True)
    
    await cq.answer("🔄 Checking balance...")
    
    balance = await get_panel_balance()
    rate = await get_usd_to_inr_rate()
    
    if balance is not None:
        inr_value = balance * rate
        text = (
            f"<b>💰 Tgbitz Panel Balance</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>💵 USD:</b> ${balance:.2f}\n"
            f"<b>💱 INR:</b> ₹{inr_value:.2f}\n"
            f"<b>📊 Rate:</b> 1 USD = ₹{rate:.2f}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Last checked: {datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC</i>"
        )
    else:
        text = (
            f"❌ <b>Failed to fetch balance</b>\n"
            f"<i>API may be down or key invalid.</i>"
        )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Refresh", callback_data=f"{S2_PREFIX}:admin:balance")],
        [InlineKeyboardButton(text="◀️ Back", callback_data=f"{S2_PREFIX}:admin:menu")]
    ])
    
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb)


# ================= Admin: View Settings =================

async def callback_s2_admin_settings(cq: CallbackQuery, state: FSMContext):
    """Show all current price settings"""
    
    await cq.answer()
    
    settings = get_all_price_settings()
    rate = await get_usd_to_inr_rate()
    global_profit = get_profit_percent()
    
    text = (
        f"<b>📋 Server 2 Price Settings</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>💱 Rate:</b> ₹{rate:.2f}/USD\n"
        f"<b>📈 Global Profit:</b> +{global_profit}%\n\n"
    )
    
    if not settings:
        text += "<i>No custom settings. All countries use global profit.</i>\n"
    else:
        text += "<b>Custom Settings:</b>\\n"
        for code, setting in settings.items():
            if setting.get("override"):
                text += f"• <code>{code}</code>: ₹{setting['custom_inr']:.2f} (Fixed)\n"
            elif "profit_percent" in setting:
                text += f"• <code>{code}</code>: +{setting['profit_percent']}% (Custom)\n"
    
    text += "\\n━━━━━━━━━━━━━━━━━━━━━"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Back", callback_data=f"{S2_PREFIX}:admin:menu")]
    ])
    
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb)


# ================= Registration Function =================

def register_server2_handlers(dp: Dispatcher, bot: Bot, users_col, orders_col, get_or_create_user, is_admin_func, ADMIN_IDS):
    """
    Register all Server 2 handlers with the dispatcher.
    Call this in bot.py after creating the dispatcher.
    """
    
    # Store references for use in handlers
    import server2_handlers as self_mod
    self_mod._bot = bot
    self_mod._users_col = users_col
    self_mod._orders_col = orders_col
    self_mod._get_or_create_user = get_or_create_user
    self_mod._is_admin = is_admin_func
    self_mod._ADMIN_IDS = ADMIN_IDS
    
    # --- User Callbacks ---
    
    @dp.callback_query(F.data == "buy_server2")
    async def _cb_buy_server2(cq: CallbackQuery, state: FSMContext):
        await callback_buy_server2(cq, state, users_col, get_or_create_user)
    
    @dp.callback_query(F.data.startswith(f"{S2_PREFIX}:page:"))
    async def _cb_s2_page(cq: CallbackQuery, state: FSMContext):
        await callback_s2_paginate(cq, state, users_col, get_or_create_user)
    
    @dp.callback_query(F.data == f"{S2_PREFIX}:search")
    async def _cb_s2_search(cq: CallbackQuery, state: FSMContext):
        await callback_s2_search(cq, state)
    
    @dp.callback_query(F.data.startswith(f"{S2_PREFIX}:country:"))
    async def _cb_s2_country(cq: CallbackQuery, state: FSMContext):
        await callback_s2_country(cq, state, users_col, get_or_create_user, orders_col, bot)
    
    @dp.callback_query(F.data.startswith(f"{S2_PREFIX}:confirm:"))
    async def _cb_s2_confirm(cq: CallbackQuery, state: FSMContext):
        await callback_s2_confirm(cq, state, users_col, get_or_create_user, orders_col, bot, is_admin_func)
    
    @dp.callback_query(F.data.startswith(f"{S2_PREFIX}:get_otp:"))
    async def _cb_s2_otp(cq: CallbackQuery, state: FSMContext):
        await callback_s2_get_otp(cq, state, bot)
    
    # --- Admin Command ---
    
    @dp.message(Command("server2"))
    async def _cmd_server2(msg: Message, state: FSMContext):
        await cmd_server2(msg, state, is_admin_func)
    
    # --- Admin Callbacks ---
    
    @dp.callback_query(F.data == f"{S2_PREFIX}:admin:menu")
    async def _cb_admin_menu(cq: CallbackQuery, state: FSMContext):
        await cmd_server2(cq.message, state, is_admin_func)
    
    @dp.callback_query(F.data == f"{S2_PREFIX}:admin:bulk")
    async def _cb_admin_bulk(cq: CallbackQuery, state: FSMContext):
        await callback_s2_admin_bulk(cq, state)
    
    @dp.callback_query(F.data == f"{S2_PREFIX}:admin:manual")
    async def _cb_admin_manual(cq: CallbackQuery, state: FSMContext):
        await callback_s2_admin_manual(cq, state)
    
    @dp.callback_query(F.data.startswith(f"{S2_PREFIX}:admin_edit:"))
    async def _cb_admin_edit(cq: CallbackQuery, state: FSMContext):
        await callback_s2_admin_edit_country(cq, state)
    
    @dp.callback_query(F.data.startswith(f"{S2_PREFIX}:admin:setprice:"))
    async def _cb_admin_set_price(cq: CallbackQuery, state: FSMContext):
        await callback_s2_admin_set_price(cq, state)
    
    @dp.callback_query(F.data.startswith(f"{S2_PREFIX}:admin:setprofit:"))
    async def _cb_admin_set_profit(cq: CallbackQuery, state: FSMContext):
        await callback_s2_admin_set_profit(cq, state)
    
    @dp.callback_query(F.data.startswith(f"{S2_PREFIX}:admin:reset:"))
    async def _cb_admin_reset(cq: CallbackQuery, state: FSMContext):
        await callback_s2_admin_reset(cq, state)
    
    @dp.callback_query(F.data == f"{S2_PREFIX}:admin:balance")
    async def _cb_admin_balance(cq: CallbackQuery, state: FSMContext):
        await callback_s2_admin_balance(cq, state)
    
    @dp.callback_query(F.data == f"{S2_PREFIX}:admin:settings")
    async def _cb_admin_settings(cq: CallbackQuery, state: FSMContext):
        await callback_s2_admin_settings(cq, state)
    
    # --- Admin State Handlers ---
    
    @dp.message(StateFilter(Server2Admin.waiting_bulk_profit))
    async def _handle_bulk(msg: Message, state: FSMContext):
        await handle_bulk_profit(msg, state)
    
    @dp.message(StateFilter(Server2Admin.waiting_custom_price))
    async def _handle_custom(msg: Message, state: FSMContext):
        await handle_custom_price(msg, state)
    
    @dp.message(StateFilter(Server2Admin.waiting_manual_price))
    async def _handle_manual(msg: Message, state: FSMContext):
        await handle_manual_price(msg, state)
    
    # --- Search State Handler ---
    
    @dp.message(StateFilter(Server2Buy.waiting_search))
    async def _handle_search(msg: Message, state: FSMContext):
        await handle_s2_search(msg, state, users_col, get_or_create_user, orders_col, bot)
    


# ================= Reusable Deep Link UI Generator for Server 2 =================
async def send_s2_country_menu_direct(target_msg: Message, country_code: str, user_id: int, username: str):
    from server2_api import get_available_countries, get_final_price, format_price_inr
    data = await get_available_countries()
    
    if not data or country_code not in data.get("countries", {}):
        return await target_msg.answer(f"❌ Country Code <b>{country_code}</b> is no longer available on Server 2.", parse_mode="HTML")
    
    country = data["countries"][country_code]
    balance = _get_or_create_user(user_id, username).get("balance", 0.0)
    _, _, _, final_inr = await get_final_price(country_code, country.get("price", "0"))
    qty = country.get("qty", 0)
    
    text = (
        f"<b>🚀 Server 2 — Account Purchase</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<blockquote><b>🌍 Country:</b> {html.escape(country.get('name', country_code))}\n"
        f"<b>📊 Stock:</b> {qty} accounts\n"
        f"<b>🏷️ Price:</b> {format_price_inr(final_inr)}</blockquote>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Your Balance:</b> ₹{balance:.2f}\n"
    )
    
    kb = InlineKeyboardBuilder()
    if balance < final_inr:
        text += f"\n❌ <b>Insufficient Balance!</b>\n<i>Shortage: ₹{final_inr - balance:.2f}</i>"
        kb.row(InlineKeyboardButton(text="💎 Recharge Now", callback_data="recharge"))
    elif qty < 1:
        text += "\n⚠️ <b>Out of Stock!</b>"
    else:
        text += "\n✅ <b>Ready to purchase?</b>"
        kb.row(InlineKeyboardButton(text=f"🛒 Buy for {format_price_inr(final_inr)}", callback_data=f"s2:confirm:{country_code}:{final_inr:.2f}"))
        
    kb.row(InlineKeyboardButton(text="Back to Main Menu", callback_data="back_main", style="danger"))
    await target_msg.answer(text, parse_mode="HTML", reply_markup=kb.as_markup(), disable_web_page_preview=True)
    
