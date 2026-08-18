#---------- © sᴛᴀʟᴋᴇʀ@hehe_stalker & Experienced Engineers
#---------- ᴘʀᴏJᴇᴄᴛ - ᴛᴇʟᴇɢʀᴀᴍ ᴀᴜᴛᴏᴍᴀᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛ sᴇʟʟɪɴɢ ʙᴏᴛ (SERVER 3 REDESIGNED)
#------------------------------------------------------------------------
import asyncio
import time
from datetime import datetime
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import provider

# ================= Anti-Spam Click Tracker =================
last_click_time = {}

def is_spamming(user_id: int, cooldown: int = 3) -> bool:
    now = time.time()
    if user_id in last_click_time and now - last_click_time[user_id] < cooldown:
        return True
    last_click_time[user_id] = now
    return False

# ================= FSM States =================
class Server3UserState(StatesGroup):
    waiting_for_search = State()

# ================= HTTP Helper Functions =================
async def fetch_api(params: dict):
    params["api_key"] = provider.API_KEY

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                provider.BASE_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:

                text = await resp.text()

                print(
                    f"[Server 3 API] "
                    f"action={params.get('action')} "
                    f"status={resp.status} "
                    f"response={text}"
                )

                if resp.status == 200:
                    return text

                print(
                    f"[Server 3 API] HTTP ERROR "
                    f"{resp.status}: {text}"
                )

    except Exception as e:
        print(f"[Server 3 API] Exception: {e}")

    return None

# ================= Handler Registration Function =================
def register_server3_handlers(dp: Dispatcher, bot: Bot, db, users_col, orders_col, is_admin_func, fmt_curr_func):
    s3_settings = db["server3_settings"]
    
    def is_maintenance_active() -> bool:
        doc = s3_settings.find_one({"_id": "maintenance_config"})
        return doc.get("enabled", False) if doc else False

    # =================================================================
    #                      ADMIN PANEL HANDLERS
    # =================================================================
    
    @dp.message(Command("server3"))
    async def admin_panel(msg: Message):
        if not is_admin_func(msg.from_user.id):
            return await msg.answer("❌ Not authorized.")
        
        m_status = "🟢 ACTIVE" if is_maintenance_active() else "🔴 DISABLED"
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Get Panel Balance", callback_data="s3_adm_balance")],
            [InlineKeyboardButton(text=f"🛠️ Toggle Maintenance ({m_status})", callback_data="s3_adm_toggle_maint")],
            [InlineKeyboardButton(text="❌ Close Menu", callback_data="admin_back")]
        ])
        await msg.answer("⚙️ <b>Server 3 (TemporaSMS) Fixed Controller</b>", reply_markup=kb)

    @dp.callback_query(F.data == "s3_adm_balance")
    async def s3_adm_balance(call: CallbackQuery):
        res = await fetch_api({"action": "getBalance"})
        if res and "ACCESS_BALANCE" in res:
            balance = res.split(":")[1]
            await call.answer(f"💳 Current Panel Balance: ₹{balance}", show_alert=True)
        else:
            await call.answer(f"⚠️ Error fetching balance: {res}", show_alert=True)

    @dp.callback_query(F.data == "s3_adm_toggle_maint")
    async def s3_adm_toggle_maint(call: CallbackQuery):
        current = is_maintenance_active()
        s3_settings.update_one({"_id": "maintenance_config"}, {"$set": {"enabled": not current}}, upsert=True)
        
        new_status = "🟢 ACTIVE" if not current else "🔴 DISABLED"
        await call.answer(f"Maintenance System updated to: {new_status}", show_alert=True)
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Get Panel Balance", callback_data="s3_adm_balance")],
            [InlineKeyboardButton(text=f"🛠️ Toggle Maintenance ({new_status})", callback_data="s3_adm_toggle_maint")],
            [InlineKeyboardButton(text="❌ Close Menu", callback_data="admin_back")]
        ])
        await call.message.edit_reply_markup(reply_markup=kb)

    @dp.message(Command("ac"))
    async def admin_check_orders(msg: Message):
        # 1. Admin Authorization Check
        if not is_admin_func(msg.from_user.id):
            return await msg.answer("❌ Not authorized.")

        status_msg = await msg.answer("⏳ <i>Fetching Server 3 order records...</i>")

        # 2. Database Queries (Sorting by timestamp descending for newest first)
        active_tasks = list(db["server3_tasks"].find({"status": "active"}).sort("timestamp", -1))
        completed_tasks = list(db["server3_tasks"].find({"status": "completed"}).sort("timestamp", -1).limit(5))
        cancelled_tasks = list(db["server3_tasks"].find({"status": "cancelled"}).sort("timestamp", -1).limit(5))

        # Helper function to get the buyer's display name or ID
        def get_buyer_info(uid):
            user_doc = users_col.find_one({"_id": uid})
            if user_doc and user_doc.get("username"):
                return f"@{user_doc['username']}"
            return f"<code>{uid}</code>"

        # 3. Format Output
        text = "📊 <b>Server 3 Order Overview</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        # --- ACTIVE ORDERS ---
        text += f"🟢 <b>Active Orders ({len(active_tasks)})</b>\n"
        if active_tasks:
            for task in active_tasks[:5]: # Show up to 5 active ones
                phone = task.get("phone", "Unknown")
                buyer = get_buyer_info(task.get("user_id"))
                text += f" ├ <code>+{phone}</code> | {buyer}\n"
            if len(active_tasks) > 5:
                text += f" └ <i>...and {len(active_tasks) - 5} more</i>\n"
        else:
            text += " └ <i>No active orders</i>\n"

        # --- COMPLETED ORDERS ---
        text += "\n✅ <b>Last 5 Completed</b>\n"
        if completed_tasks:
            for task in completed_tasks:
                phone = task.get("phone", "Unknown")
                buyer = get_buyer_info(task.get("user_id"))
                otp = task.get("otp", "No OTP")
                text += f" ├ <code>+{phone}</code> | {buyer} \n"
                text += f" │  └ OTP: <span class='tg-spoiler'>{otp}</span>\n"
        else:
            text += " └ <i>No completed orders yet</i>\n"

        # --- CANCELLED ORDERS ---
        text += "\n❌ <b>Last 5 Cancelled</b>\n"
        if cancelled_tasks:
            for task in cancelled_tasks:
                phone = task.get("phone", "Unknown")
                buyer = get_buyer_info(task.get("user_id"))
                text += f" ├ <code>+{phone}</code> | {buyer}\n"
        else:
            text += " └ <i>No cancelled orders yet</i>\n"

        # 4. Send Response
        await status_msg.edit_text(text)
        

    # =================================================================
    #                      USER MENU INTERFACES
    # =================================================================
    
    @dp.callback_query(F.data == "s3_user_root")
    async def user_server3_menu(call: CallbackQuery):
        if is_maintenance_active():
            return await call.answer("⚠️ Server 3 is currently undergoing maintenance. Please try again later!", show_alert=True)
            
        text = (
            " <b>Server 3 - OTP activation/Number change</b>\n"
            "-----------------------•\n"
            "- Get fresh numbers that don't have account\n"
            "- Create new accounts or change number\n"
            "- Dynamic carrier operator mapping active"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Telegram (NUM change)", callback_data="s3_usrsrv:tg:0", icon_custom_emoji_id="6296218646284863141", style="primary")
            ],
            [
                InlineKeyboardButton(text="WhatsApp", callback_data="s3_usrsrv:wa:0", icon_custom_emoji_id="5935973359480213803", style="success")
            ],
            [InlineKeyboardButton(text="Back", callback_data="buy", icon_custom_emoji_id="5409284148491726576", style="danger")]
        ])
        await call.message.edit_text(text, reply_markup=kb)

    # STEP 1: Show Unique Countries Available for Service
    @dp.callback_query(F.data.startswith("s3_usrsrv:"))
    async def user_list_countries(call: CallbackQuery, search_query: str = None):
        if is_maintenance_active():
            return await call.answer("⚠️ This system server has been paused by the administration.", show_alert=True)
            
        parts = call.data.split(":")
        service = parts[1]
        page = int(parts[2])
        
        all_offers = provider.get_active_offers(service)
        
        # Pull out unique names preserving manual order arrays
        unique_countries = []
        for o in all_offers:
            if o["country"] not in unique_countries:
                unique_countries.append(o["country"])
                
        if search_query:
            q = search_query.lower()
            unique_countries = [c for c in unique_countries if q in c.lower()]

        if service == "wa":
            text = (
                f'<tg-emoji emoji-id="5346024644635804737">🥂</tg-emoji> <b>Select Country to Change/Buy <tg-emoji emoji-id="5345943173401175849">🥂</tg-emoji> num </b>\n'
                f'<blockquote><tg-emoji emoji-id="5408943604829794451">🥂</tg-emoji> <b>Points to Remember for Buying/Changing Whats@pp Number</b></blockquote>\n'
                f'<tg-emoji emoji-id="5348129380474306311">🥂</tg-emoji> <i>Read carefully before changing/Buying num </i>\n'
                f'<blockquote expandable>1. Buy num and change num , bot will send otp automatically once it is send.\n2. If it shows there is already acc on this num / ban , then cancel and buy again your money will be refunded\n3. Otp will be given only once , so change using other device/app if u back then u might loss the num .</blockquote>'
            )
        else:
            text = (
                f'<tg-emoji emoji-id="5346024644635804737">🥂</tg-emoji> <b>Select Country to change <tg-emoji emoji-id="6296218646284863141">🥂</tg-emoji> num </b>\n'
                f'<blockquote><tg-emoji emoji-id="5408943604829794451">🥂</tg-emoji> <b>Points to Remember</b></blockquote>\n'
                f'<tg-emoji emoji-id="5348129380474306311">🥂</tg-emoji> <i>Read carefully before changing num </i>\n'
                f'<blockquote expandable>1. Buy num and change num , bot will send otp automatically once it is send.\n2. If it shows there is already acc on this num / ban , then cancel and buy again your money will be refunded\n3. Otp will be given only once , so change using other device/app if u back then u might loss the num .</blockquote>'
            )
            
        
        if not unique_countries:
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="s3_user_root")]])
            return await call.message.edit_text("⚠️ No matching countries found.", reply_markup=kb)
            
        per_page = 14
        total_pages = max(1, (len(unique_countries) + per_page - 1) // per_page)
        page = min(page, total_pages - 1)
        
        start_idx = page * per_page
        sliced_countries = unique_countries[start_idx:start_idx + per_page]
        kb = InlineKeyboardBuilder()
        for country in sliced_countries:
            # Fetch flag from provider config, fallback to default bullet if not found
            flag = provider.COUNTRY_FLAGS.get(country.lower(), "▪️")
            kb.button(text=f"{flag} {country}", callback_data=f"s3_country:{service}:{country}")
            
        kb.adjust(2) # Show countries beautifully in two columns

        nav_buttons = []
        for p_idx in range(total_pages):
            btn_txt = f"[{p_idx + 1}]" if p_idx == page else f"{p_idx + 1}"
            nav_buttons.append(InlineKeyboardButton(text=btn_txt, callback_data=f"s3_usrsrv:{service}:{p_idx}"))
            
        if nav_buttons and total_pages > 1:
            kb.row(*nav_buttons)
            
        kb.row(
            InlineKeyboardButton(text="Search", callback_data=f"s3_search_prompt:{service}", icon_custom_emoji_id="5429571366384842791", style="success"),
            InlineKeyboardButton(text="Back Menu", callback_data="s3_user_root", icon_custom_emoji_id="5409284148491726576", style="danger")
        )
        await call.message.edit_text(text, reply_markup=kb.as_markup())

    # STEP 2: Show Operators Available for the Selected Country
    @dp.callback_query(F.data.startswith("s3_country:"))
    async def user_list_operators(call: CallbackQuery):
        if is_maintenance_active():
            return await call.answer("⚠️ This system server has been paused by the administration.", show_alert=True)
            
        parts = call.data.split(":")
        service = parts[1]
        country_name = parts[2]
        
        all_offers = provider.get_active_offers(service)
        country_offers = [o for o in all_offers if o["country"].lower() == country_name.lower()]
        flag = provider.COUNTRY_FLAGS.get(country_name.lower(), "▪️")
        text = (
            f"- <b>Available Operators for this server</b>\n"
            f"-----------------------•\n"
            f"▪️ <b>Country</b>: {flag} {country_name}\n"
            f"-----------------------•\n"
            f"<blockquote expandable><i>• For Telegram, use only for number change</i>\n"
            f"<i>• For WhatsApp, only use official WhatsApp or WhatsApp business</i></blockquote>"
        )
        
        kb = InlineKeyboardBuilder()
        for offer in country_offers:
            btn_label = f"Operator {offer['operator']} ➜ {fmt_curr_func(offer['bot_price'])}"
            kb.button(text=btn_label, callback_data=f"s3_buy_ask:{offer['index']}")
            
        kb.adjust(1)
        kb.row(InlineKeyboardButton(text="Back to Countries", callback_data=f"s3_usrsrv:{service}:0", icon_custom_emoji_id="5409284148491726576", style="danger"))
        
        await call.message.edit_text(text, reply_markup=kb.as_markup())

    @dp.callback_query(F.data.startswith("s3_search_prompt:"))
    async def s3_search_prompt(call: CallbackQuery, state: FSMContext):
        service = call.data.split(":")[1]
        await call.message.edit_text("🔍 <b>Enter country name to filter active configurations:</b>")
        await state.update_data(srv=service)
        await state.set_state(Server3UserState.waiting_for_search)

    @dp.message(StateFilter(Server3UserState.waiting_for_search))
    async def s3_search_handler(msg: Message, state: FSMContext):
        data = await state.get_data()
        await state.clear()
        
        dummy_call = CallbackQuery(
            id="0", from_user=msg.from_user, chat_instance="0",
            message=await msg.answer("⏳ Processing inventory records..."), data=f"s3_usrsrv:{data['srv']}:0"
        )
        await user_list_countries(dummy_call, search_query=msg.text.strip())

    # STEP 3: Order Review Window Formatted with Your Exact SMM Style Layout Template
    @dp.callback_query(F.data.startswith("s3_buy_ask:"))
    async def s3_user_buy_ask(call: CallbackQuery):
        offer_idx = int(call.data.split(":")[1])
        srv, country, op, max_p, bot_p = provider.MANUAL_CONFIG[offer_idx]
        
        service_title = "Telegram Number Change" if srv == "tg" else "WhatsApp "
        
        text = (
            f"<b>How do you want buy-(VIRTUAL)</b>\n"
            f"––––––––––––––————––•\n"
            f"• <b>Service</b>  →  {service_title}\n"
            f"• <b>Country</b>  →  {country}\n"
            f"• <u>Operator</u>  →  Operator {op}\n"
            f"• <u>Price</u>  →  {fmt_curr_func(bot_p)}/each\n"
            f"• <u>Min Buy</u>  →  1"
        )
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Proceed to Purchase", callback_data=f"s3_buy_terms:{offer_idx}", style="success")],
            [InlineKeyboardButton(text="Back Operators", callback_data=f"s3_country:{srv}:{country}", icon_custom_emoji_id="5409284148491726576", style="danger")]
        ])
        await call.message.edit_text(text, reply_markup=kb)

    @dp.callback_query(F.data.startswith("s3_buy_terms:"))
    async def s3_buy_terms(call: CallbackQuery):
        if is_spamming(call.from_user.id, cooldown=3):
            return await call.answer("⏳ Protection active! Please wait 3 seconds.", show_alert=True)
            
        offer_idx = int(call.data.split(":")[1])
        srv, country, op, max_p, bot_p = provider.MANUAL_CONFIG[offer_idx]
        
        user_doc = users_col.find_one({"_id": call.from_user.id})
        bal = user_doc.get("balance", 0.0) if user_doc else 0.0
        
        if bal < bot_p:
            return await call.answer("❌ Insufficient system wallet balance allocation.", show_alert=True)
            
        terms_txt = (
            "⚠️ <b>Important Activation Rules</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "• This configuration item is <b>non-refundable</b> once a verification code arrives.\n"
            "• If no OTP is received within 5 minutes, the system auto-cancels and refunds completely."
        )
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Accept and Order", callback_data=f"s3_exec_buy:{offer_idx}", style="success")],
            [InlineKeyboardButton(text="❌ Decline", callback_data=f"s3_country:{srv}:{country}", style="danger")]
        ])
        await call.message.edit_text(terms_txt, reply_markup=kb)

    @dp.callback_query(F.data.startswith("s3_exec_buy:"))
    async def s3_execute_purchase(call: CallbackQuery):
        # Anti-double purchase system freeze implementation (1 click per 3 seconds)
        if is_spamming(call.from_user.id, cooldown=3):
            return await call.answer("⏳ Order execution frozen! Please wait 3 seconds between requests.", show_alert=True)
            
        offer_idx = int(call.data.split(":")[1])
        user_id = call.from_user.id
        
        user_doc = users_col.find_one({"_id": user_id})
        bal = user_doc.get("balance", 0.0) if user_doc else 0.0
        
        srv, country, op, max_p, bot_p = provider.MANUAL_CONFIG[offer_idx]
        c_id = provider.COUNTRY_IDS.get(country.lower(), {}).get(op)
        srv_code = provider.OPERATOR_SERVICES.get(op, {}).get(srv)
        
        if bal < bot_p:
            return await call.message.edit_text("❌ Verification failed: Insufficient account funds.")
            
        await call.message.edit_text("⏳ <i>Assigning Number please wait..</i>")
        
        params = {
            "action": "getNumber",
            "service": srv_code,
            "country": c_id,
            "operator": op,
            "maxPrice": str(max_p)
        }
        
        api_res = await fetch_api(params)
        res_str = str(api_res)
        
        if "ACCESS_NUMBER" in res_str:
            parts = res_str.split(":")
            act_id = parts[1]
            phone = parts[2].strip()
        else:
            # Added error keyboard for No Stock scenario
            err_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Buy Again", callback_data=f"s3_buy_ask:{offer_idx}")],
                [InlineKeyboardButton(text="Back Menu", callback_data="back_main", icon_custom_emoji_id="5409284148491726576", style="danger")]
            ])
            return await call.message.edit_text("❌ <b>NO STOCK available for this configuration.</b>", reply_markup=err_kb)
            
        db["server3_tasks"].insert_one({
            "activation_id": act_id, "user_id": user_id, "phone": phone,
            "price": bot_p, "service": srv, "country": country, "operator": op,
            "timestamp": time.time(), "status": "active"
        })
        
        # Added 'offer_idx' as the last argument passed to the worker
        asyncio.create_task(poll_otp_worker(bot, act_id, user_id, call.message.message_id, phone, srv, country, op, bot_p, db, users_col, orders_col, fmt_curr_func, offer_idx))

    # =================================================================
    #                      OTP BACKGROUND WORKER LOOP
    # =================================================================
    
    async def poll_otp_worker(bot_instance: Bot, act_id: str, user_id: int, msg_id: int, phone: str, service: str, country: str, op: str, price: float, database, u_col, o_col, fmt_func, offer_idx: int):
        start_t = time.time()
        # Changed execution scope lifespan cycle limit loop threshold window to exactly 5 minutes (300 seconds)
        while time.time() - start_t < 300:
            t_doc = database["server3_tasks"].find_one({"activation_id": act_id})
            if not t_doc or t_doc.get("status") == "cancelled":
                return
                
            status_res = await fetch_api({"action": "getStatus", "id": act_id})
            
            if status_res and "STATUS_OK" in status_res:
                otp_code = status_res.split(":")[1]
                
                u_col.update_one({"_id": user_id}, {"$inc": {"balance": -price}})
                database["server3_tasks"].update_one({"activation_id": act_id}, {"$set": {"status": "completed", "otp": otp_code}})
                
                o_col.insert_one({
                    "user_id": user_id, "number": phone, "service": service, "price": price,
                    "otp": otp_code, "server": "Server 3", "status": "purchased", "date": datetime.utcnow()
                })
                
                try:
                    await bot_instance.edit_message_text(
                        chat_id=user_id, message_id=msg_id,
                        text=(
                            f"✅ <b><u>Order Completed Successfully</u>!</b>\n\n"
                            f"▪️<b>Number:</b> <code>+{phone}</code>\n"
                            f"▪️<b>Country:</b> {country}\n"
                            f"▪️<b>Operator:</b> Operator {op}\n"
                            f"▪️<b>OTP Received:</b> <code>{otp_code}</code>\n"
                            f"▪️<b>Platform Target:</b> {service.upper()}"
                        ), reply_markup=None
                    )
                except Exception as e:
                    print(f"UI Complete View Layout presentation error: {e}")
                    
                user_record = u_col.find_one({"_id": user_id}) or {}
                username = user_record.get("username", f"User_{user_id}")
                flag = provider.COUNTRY_FLAGS.get(country.lower(), "▪️")
                # 1. Map the service name string dynamically 
                sales_service_name = "TG number change" if service.lower() == "tg" else service.upper()

                sales_log = (
                    f"✅ <b>New Server 3 Purchase</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"➖ <b><u>Service</u>:</b> {sales_service_name}\n"
                    f"➖ <b><u>Country</u>:</b> {flag} {country}\n"
                    f"➕ <b><u>Operator</u>: </b>{op} 🍷\n"
                    f"➕ <b>Nxmbxr:</b> <code>+{phone[:6]}•••••</code>\n"
                    f"➕ <b>CD:</b> <span class='tg-spoiler'>{otp_code}</span>\n"
                    f"💳 <b>Price:</b> {fmt_func(price)}"
                )
                admin_log = (
                    f"📢 <b>Server 3 Purchase Alert</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 <b>User:</b> @{username} (<code>{user_id}</code>)\n"
                    f"📞 <b>Number:</b> <code>+{phone}</code>\n"
                    f"🌍 <b>Country:</b> {country} (Op {op})\n"
                    f"💬 <b>OTP Code:</b> <code>{otp_code}</code>\n"
                    f"💳 <b>Debited:</b> {fmt_func(price)}"
                )
                
                # 2. Build the inline button for the channel sales feed
                                # --- DYNAMIC DEEP LINK FOR SERVER 3 LOGS ---
                clean_country_param = country.replace(" ", "_")
                bot_me = await bot_instance.get_me()
                sales_kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text=f"🛒 Buy {country} Now", 
                        url=f"https://t.me/{bot_me.username}?start=buy_s3_{service}_{clean_country_param}", 
                        style="success"
                    )]
                ])

                try:
                    # 3. Pass the inline keyboard markup to the channel dispatch
                    await bot_instance.send_message("-1004484806488", sales_log, reply_markup=sales_kb)
                    await bot_instance.send_message("-1004492615113", admin_log)
                except Exception as log_err:
                    print(f"Log dispatch failure: {log_err}")
                return
            
            elif status_res == "STATUS_CANCEL":
                database["server3_tasks"].update_one({"activation_id": act_id}, {"$set": {"status": "cancelled"}})
                err_kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Buy Again", callback_data=f"s3_buy_ask:{offer_idx}")],
                    [InlineKeyboardButton(text="🔙 Back Menu", callback_data="back_main")]
                ])
                await bot_instance.edit_message_text(
                    chat_id=user_id, message_id=msg_id, 
                    text="❌ <b>Order was cancelled or timed out by the provisioning provider.</b>", 
                    reply_markup=err_kb
                )
                return

                
            kb = InlineKeyboardBuilder()
            elapsed_time = time.time() - start_t
            
            # Dynamic text visualization rendering rules based on real-time elapsed allocation windows
            if elapsed_time < 180:
                remaining_lock = int(180 - elapsed_time)
                kb.button(text=f"🔒 Cancel lock ({remaining_lock}s)", callback_data=f"s3_user_cancel:{act_id}", style="danger")
            else:
                kb.button(text="🛑 Cancel Order", callback_data=f"s3_user_cancel:{act_id}", style="success")
            
            try:
                await bot_instance.edit_message_text(
                    chat_id=user_id, message_id=msg_id,
                    text=(
                        f"<blockquote>✅<b>Number Purchased Successfully</b></blockquote>\n"
                        f"-----------------------------•\n"
                        f"➖ <b><u>Number</u>:</b> <code>+{phone}</code>\n"
                        f"➖ <b><u>Country</u>:</b> {country}\n"
                        f"🍷 <b><u>Operator</u>:</b> Operator {op}\n"
                        f"💬 <b><u>OTP Code</u>:</b> <code>Waiting for message...</code>\n"
                        f"➕ <b><u>Service</u>:</b> {service.upper()}\n\n"
                        f"<blockquote expandable><i>OTP will be received automatically. you can only cancel after 3 minutes of no OTP also it'll be automatically cancelled if OTP isn't recieved within 5 Minutes</i></blockquote>"
                    ), reply_markup=kb.as_markup()
                )
            except:
                pass
                
            await asyncio.sleep(4)
            
        t_doc = database["server3_tasks"].find_one({"activation_id": act_id})
        if t_doc and t_doc.get("status") == "active":
            # Direct automatic cancel interaction via panel using status=8 API parameters post 5 minutes
            await fetch_api({"action": "setStatus", "status": "8", "id": act_id})
            database["server3_tasks"].update_one({"activation_id": act_id}, {"$set": {"status": "cancelled"}})
            try:
                err_kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Buy Again", callback_data=f"s3_buy_ask:{offer_idx}")],
                    [InlineKeyboardButton(text="🔙 Back Menu", callback_data="back_main")]
                ])
                await bot_instance.edit_message_text(
                    chat_id=user_id, message_id=msg_id, 
                    text="⏱️ <b>Order Timed Out!</b> No verification OTP was detected within the 5-minute limit. System auto-refunded.",
                    reply_markup=err_kb
                )
            except:
                pass

    @dp.callback_query(F.data.startswith("s3_user_cancel:"))
    async def s3_user_cancel_order(call: CallbackQuery):
        act_id = call.data.split(":")[1]
        
        task_info = db["server3_tasks"].find_one({"activation_id": act_id})
        if task_info:
            elapsed = time.time() - task_info.get("timestamp", 0)
            if elapsed < 180:
                wait_left = int(180 - elapsed)
                return await call.answer(f"⚠️ You can only cancel this number after 3 minutes of no OTP. (Wait {wait_left}s)", show_alert=True)
        
        # Explicit cancel instruction sequence execution forwarded onto panel endpoint using configuration parameters
        await fetch_api({"action": "setStatus", "status": "8", "id": act_id})
        db["server3_tasks"].update_one({"activation_id": act_id}, {"$set": {"status": "cancelled"}})
        
        await call.answer("✅ Order cancelled successfully. No charges were made.", show_alert=True)
        await call.message.edit_text("🛑 <b>Activation Terminated!</b>\n- Balance Refunded!")


# ================= Reusable Deep Link UI Generator for Server 3 =================
async def send_s3_operator_menu_direct(target_msg: Message, service: str, country_name: str, fmt_curr_func):
    import provider
    all_offers = provider.get_active_offers(service)
    country_offers = [o for o in all_offers if o["country"].lower() == country_name.lower()]
    
    if not country_offers:
        return await target_msg.answer(f"❌ <b>{country_name}</b> is currently out of stock on Server 3.", parse_mode="HTML")
        
    flag = provider.COUNTRY_FLAGS.get(country_name.lower(), "▪️")
    text = (
        f"- <b>Available Operators for this server</b>\n"
        f"-----------------------•\n"
        f"▪️ <b>Country</b>: {flag} {country_name}\n"
        f"-----------------------•\n"
        f"<blockquote expandable><i>• For Telegram, use only for number change</i>\n"
        f"<i>• For WhatsApp, only use official WhatsApp or WhatsApp business</i></blockquote>"
    )
    
    kb = InlineKeyboardBuilder()
    for offer in country_offers:
        btn_label = f"Operator {offer['operator']} ➜ {fmt_curr_func(offer['bot_price'])}"
        kb.button(text=btn_label, callback_data=f"s3_buy_ask:{offer['index']}")
        
    kb.adjust(1)
    kb.row(InlineKeyboardButton(text="Back to Main Menu", callback_data="back_main", style="danger"))
    await target_msg.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
        
