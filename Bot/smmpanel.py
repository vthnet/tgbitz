import os
import json
import time
import aiohttp
import urllib.parse
from datetime import datetime, timezone
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bson.objectid import ObjectId

# Router Setup
router = Router()

# API Configuration
API_KEY = "1ecbe38e187c39497fb30ea3a2946435"
API_URL = "https://cheapestsmmpanels.com/api/v2"

# Anti-spam cache
click_cache = {}

# --- FSM States ---
class SMMAdminState(StatesGroup):
    waiting_app_name = State()
    waiting_app_emoji = State()
    waiting_service_app = State()
    waiting_service_id = State()
    waiting_service_price = State()
    waiting_service_min_max = State()
    waiting_service_name = State()
    
    waiting_edit_app_name = State()
    waiting_edit_srv_name = State()
    waiting_edit_srv_price = State()
    waiting_edit_srv_minmax = State()

class SMMUserState(StatesGroup):
    waiting_link = State()
    waiting_quantity = State()
    waiting_search = State()

# --- Helper Functions ---
async def call_api(action: str, **kwargs):
    url = f"{API_URL}?key={API_KEY}&action={action}"
    for k, v in kwargs.items():
        if k == "link":
            v = urllib.parse.quote(v, safe='')
        url += f"&{k}={v}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            try:
                # Read as text first to bypass strict JSON content-type header checks
                raw_text = await response.text()
                return json.loads(raw_text)
            except Exception:
                return {"error": "Invalid API Response"}

def fmt_curr(amount):
    return f"₹{amount:.2f}"

def mask_user_id(user_id):
    """Masks the user ID for public logs"""
    u_str = str(user_id)
    if len(u_str) <= 4:
        return u_str
    return u_str[:3] + "****" + u_str[-3:]

def is_admin(user_id, db):
    admin_doc = db["admins"].find_one({"_id": user_id})
    return user_id in [8021449673, 233444460] or admin_doc is not None

# Global helper to ensure message deletion works if not caught elsewhere
@router.callback_query(F.data == "delete_msg")
async def delete_msg_handler(cq: CallbackQuery):
    try:
        await cq.message.delete()
    except:
        pass
    await cq.answer()


# ==========================================
#               ADMIN PANEL
# ==========================================

async def show_admin_panel(message: Message, db, edit_msg=False):
    api_resp = await call_api("balance")
    balance = api_resp.get("balance", "Error fetching")
    currency = api_resp.get("currency", "USD")

    text = (
        f"<b>⚙️ External SMM Admin Panel</b>\n"
        f"––––––—–————––––——–––•\n"
        f"<blockquote>💰 <b>Panel Balance:</b> {balance} {currency}</blockquote>\n\n"
        f"<i>Select an action below to manage external SMM services.</i>"
    )

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="➕ Add App", callback_data="smm_add_app"),
           InlineKeyboardButton(text="➕ Add Service", callback_data="smm_add_service"))
    kb.row(InlineKeyboardButton(text="✏️ Edit App", callback_data="smm_edit_app"),
           InlineKeyboardButton(text="✏️ Edit Service", callback_data="smm_edit_service"))
    kb.row(InlineKeyboardButton(text="🗑️ Remove App", callback_data="smm_rm_app"),
           InlineKeyboardButton(text="🗑️ Remove Service", callback_data="smm_rm_service"))
    kb.row(InlineKeyboardButton(text="🔙 Close", callback_data="delete_msg", icon_custom_emoji_id="5409284148491726576", style="danger"))

    if edit_msg:
        await message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())

@router.message(Command("smmpanel"))
async def cmd_smmpanel(msg: Message, db, state: FSMContext):
    if not is_admin(msg.from_user.id, db):
        return await msg.answer("❌ Not authorized.")
    await state.clear()
    await show_admin_panel(msg, db, edit_msg=False)

@router.callback_query(F.data == "smm_admin_main")
async def cq_admin_main(cq: CallbackQuery, db, state: FSMContext):
    if not is_admin(cq.from_user.id, db):
        return await cq.answer("❌ Not authorized.", show_alert=True)
    await state.clear()
    await show_admin_panel(cq.message, db, edit_msg=True)
    await cq.answer()

# --- ADD APP ---
@router.callback_query(F.data == "smm_add_app")
async def add_app_start(cq: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🔙 Back", callback_data="smm_admin_main", icon_custom_emoji_id="5409284148491726576", style="danger"))
    await cq.message.edit_text("📝 <b>Send the Name of the App</b> (e.g., Instagram, YouTube):", parse_mode="HTML", reply_markup=kb.as_markup())
    await state.set_state(SMMAdminState.waiting_app_name)
    await cq.answer()

@router.message(StateFilter(SMMAdminState.waiting_app_name))
async def add_app_name(msg: Message, state: FSMContext):
    await state.update_data(app_name=msg.text.strip())
    await msg.answer("✨ <b>Now, send the name again but include the Premium Emoji icon you want for the button.</b>\n<i>(I will extract the emoji ID automatically)</i>", parse_mode="HTML")
    await state.set_state(SMMAdminState.waiting_app_emoji)

@router.message(StateFilter(SMMAdminState.waiting_app_emoji))
async def add_app_emoji(msg: Message, state: FSMContext, db):
    data = await state.get_data()
    emoji_id = None
    
    if msg.entities:
        for ent in msg.entities:
            if ent.type == "custom_emoji":
                emoji_id = ent.custom_emoji_id
                break

    db["smm_apps"].insert_one({
        "name": data["app_name"],
        "emoji_id": emoji_id
    })

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🔙 Back to Admin", callback_data="smm_admin_main", icon_custom_emoji_id="5409284148491726576", style="danger"))
    await msg.answer(f"✅ <b>App {data['app_name']} added successfully!</b>", parse_mode="HTML", reply_markup=kb.as_markup())
    await state.clear()

# --- ADD SERVICE ---
@router.callback_query(F.data == "smm_add_service")
async def add_srv_start(cq: CallbackQuery, state: FSMContext, db):
    apps = list(db["smm_apps"].find({}))
    if not apps:
        return await cq.answer("⚠️ Add an app first!", show_alert=True)

    kb = InlineKeyboardBuilder()
    for app in apps:
        kwargs = {"text": app["name"], "callback_data": f"smm_sel_app:{str(app['_id'])}"}
        if app.get("emoji_id"):
            kwargs["icon_custom_emoji_id"] = app["emoji_id"]
        kb.row(InlineKeyboardButton(**kwargs))
    kb.row(InlineKeyboardButton(text="🔙 Cancel", callback_data="smm_admin_main", icon_custom_emoji_id="5409284148491726576", style="danger"))
    
    await cq.message.edit_text("📱 <b>Select the App for this new service:</b>", parse_mode="HTML", reply_markup=kb.as_markup())
    await state.set_state(SMMAdminState.waiting_service_app)
    await cq.answer()

@router.callback_query(StateFilter(SMMAdminState.waiting_service_app), F.data.startswith("smm_sel_app:"))
async def add_srv_app_selected(cq: CallbackQuery, state: FSMContext):
    app_id = cq.data.split(":")[1]
    await state.update_data(app_id=app_id)
    await cq.message.edit_text("🆔 <b>Send the Service ID</b> (From panel API list - Numbers only):", parse_mode="HTML")
    await state.set_state(SMMAdminState.waiting_service_id)
    await cq.answer()

@router.callback_query(F.data.startswith("smm_add_srv_again:"))
async def add_srv_again(cq: CallbackQuery, state: FSMContext):
    app_id = cq.data.split(":")[1]
    await state.update_data(app_id=app_id)
    await cq.message.edit_text("🆔 <b>Send the next Service ID</b> (From panel API list - Numbers only):", parse_mode="HTML")
    await state.set_state(SMMAdminState.waiting_service_id)
    await cq.answer()

@router.message(StateFilter(SMMAdminState.waiting_service_id))
async def add_srv_id(msg: Message, state: FSMContext):
    service_id = msg.text.strip()
    if not service_id.isdigit():
        return await msg.answer("❌ <b>Invalid Input!</b> Service ID must contain ONLY numbers. Please send a valid ID:", parse_mode="HTML")
        
    await state.update_data(service_id=service_id)
    await msg.answer("📝 <b>Send the Service Name</b> (e.g., Instagram Likes - Fast):", parse_mode="HTML")
    await state.set_state(SMMAdminState.waiting_service_name)

@router.message(StateFilter(SMMAdminState.waiting_service_name))
async def add_srv_name(msg: Message, state: FSMContext):
    await state.update_data(service_name=msg.text.strip())
    await msg.answer("💰 <b>Send the Price per 1000</b> (in ₹):", parse_mode="HTML")
    await state.set_state(SMMAdminState.waiting_service_price)

@router.message(StateFilter(SMMAdminState.waiting_service_price))
async def add_srv_price(msg: Message, state: FSMContext):
    try:
        price_val = float(msg.text.strip())
    except ValueError:
        return await msg.answer("❌ Invalid price format. Use numbers.")
    await state.update_data(price=price_val)
    await msg.answer("📊 <b>Send Min and Max quantity</b> separated by comma (e.g., 10,10000):", parse_mode="HTML")
    await state.set_state(SMMAdminState.waiting_service_min_max)

@router.message(StateFilter(SMMAdminState.waiting_service_min_max))
async def add_srv_minmax(msg: Message, state: FSMContext, db):
    try:
        min_q, max_q = msg.text.split(",")
        min_val = int(min_q.strip())
        max_val = int(max_q.strip())
    except ValueError:
        return await msg.answer("❌ Invalid format. Please send like: 10,10000")

    data = await state.get_data()
    
    srv_doc = {
        "app_id": data["app_id"],
        "service_id": data["service_id"],
        "name": data["service_name"],
        "price": data["price"],
        "min": min_val,
        "max": max_val
    }
    
    db["smm_services"].insert_one(srv_doc)
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="➕ Add Another to Same App", callback_data=f"smm_add_srv_again:{data['app_id']}"))
    kb.row(InlineKeyboardButton(text="🔙 Admin Menu", callback_data="smm_admin_main", icon_custom_emoji_id="5409284148491726576", style="danger"))

    await msg.answer(f"✅ <b>Service {data['service_name']} added successfully!</b>", parse_mode="HTML", reply_markup=kb.as_markup())
    await state.clear()


# --- EDIT APP ---
@router.callback_query(F.data == "smm_edit_app")
async def edit_app_start(cq: CallbackQuery, db):
    apps = list(db["smm_apps"].find({}))
    if not apps:
        return await cq.answer("⚠️ No apps to edit!", show_alert=True)

    kb = InlineKeyboardBuilder()
    for app in apps:
        kb.row(InlineKeyboardButton(text=f"✏️ {app['name']}", callback_data=f"smm_ea_sel:{str(app['_id'])}"))
    kb.row(InlineKeyboardButton(text="🔙 Back", callback_data="smm_admin_main", icon_custom_emoji_id="5409284148491726576", style="danger"))
    
    await cq.message.edit_text("📱 <b>Select the App you want to edit:</b>", parse_mode="HTML", reply_markup=kb.as_markup())
    await cq.answer()

@router.callback_query(F.data.startswith("smm_ea_sel:"))
async def edit_app_selected(cq: CallbackQuery, state: FSMContext):
    app_id = cq.data.split(":")[1]
    await state.update_data(app_id=app_id)
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🔙 Cancel", callback_data="smm_edit_app", icon_custom_emoji_id="5409284148491726576", style="danger"))
    await cq.message.edit_text("📝 <b>Send the NEW Name for this App:</b>", parse_mode="HTML", reply_markup=kb.as_markup())
    await state.set_state(SMMAdminState.waiting_edit_app_name)
    await cq.answer()

@router.message(StateFilter(SMMAdminState.waiting_edit_app_name))
async def edit_app_save(msg: Message, state: FSMContext, db):
    data = await state.get_data()
    new_name = msg.text.strip()
    
    db["smm_apps"].update_one(
        {"_id": ObjectId(data["app_id"])},
        {"$set": {"name": new_name}}
    )
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🔙 Back to Admin", callback_data="smm_admin_main", icon_custom_emoji_id="5409284148491726576", style="danger"))
    await msg.answer(f"✅ <b>App name updated to:</b> {new_name}", parse_mode="HTML", reply_markup=kb.as_markup())
    await state.clear()


# --- EDIT SERVICE ---
@router.callback_query(F.data == "smm_edit_service")
async def edit_srv_app_start(cq: CallbackQuery, db):
    apps = list(db["smm_apps"].find({}))
    if not apps:
        return await cq.answer("⚠️ No apps found!", show_alert=True)

    kb = InlineKeyboardBuilder()
    for app in apps:
        kb.row(InlineKeyboardButton(text=app["name"], callback_data=f"smm_es_app:{str(app['_id'])}"))
    kb.row(InlineKeyboardButton(text="🔙 Back", callback_data="smm_admin_main", icon_custom_emoji_id="5409284148491726576", style="danger"))
    
    await cq.message.edit_text("📱 <b>Select the App containing the service to edit:</b>", parse_mode="HTML", reply_markup=kb.as_markup())
    await cq.answer()

@router.callback_query(F.data.startswith("smm_es_app:"))
async def edit_srv_list(cq: CallbackQuery, db):
    app_id = cq.data.split(":")[1]
    services = list(db["smm_services"].find({"app_id": app_id}))
    
    if not services:
        return await cq.answer("⚠️ No services under this app!", show_alert=True)

    kb = InlineKeyboardBuilder()
    for srv in services:
        kb.row(InlineKeyboardButton(text=f"{srv['name']} - {fmt_curr(srv['price'])}", callback_data=f"smm_es_srv:{str(srv['_id'])}"))
    kb.row(InlineKeyboardButton(text="🔙 Back", callback_data="smm_edit_service", icon_custom_emoji_id="5409284148491726576", style="danger"))
    
    await cq.message.edit_text("🏷️ <b>Select the Service to Edit:</b>", parse_mode="HTML", reply_markup=kb.as_markup())
    await cq.answer()

@router.callback_query(F.data.startswith("smm_es_srv:"))
async def edit_srv_selected(cq: CallbackQuery, state: FSMContext, db):
    srv_id = cq.data.split(":")[1]
    await state.update_data(srv_id=srv_id)
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🔙 Cancel", callback_data="smm_edit_service", icon_custom_emoji_id="5409284148491726576", style="danger"))
    await cq.message.edit_text("📝 <b>Send the NEW Service Name:</b>", parse_mode="HTML", reply_markup=kb.as_markup())
    await state.set_state(SMMAdminState.waiting_edit_srv_name)
    await cq.answer()

@router.message(StateFilter(SMMAdminState.waiting_edit_srv_name))
async def edit_srv_name(msg: Message, state: FSMContext):
    await state.update_data(srv_name=msg.text.strip())
    await msg.answer("💰 <b>Send the NEW Price per 1000 (in ₹):</b>", parse_mode="HTML")
    await state.set_state(SMMAdminState.waiting_edit_srv_price)

@router.message(StateFilter(SMMAdminState.waiting_edit_srv_price))
async def edit_srv_price(msg: Message, state: FSMContext):
    try:
        price_val = float(msg.text.strip())
    except ValueError:
        return await msg.answer("❌ Invalid price format. Use numbers.")
    await state.update_data(srv_price=price_val)
    await msg.answer("📊 <b>Send the NEW Min and Max quantity</b> separated by comma (e.g., 10,10000):", parse_mode="HTML")
    await state.set_state(SMMAdminState.waiting_edit_srv_minmax)

@router.message(StateFilter(SMMAdminState.waiting_edit_srv_minmax))
async def edit_srv_save(msg: Message, state: FSMContext, db):
    try:
        min_q, max_q = msg.text.split(",")
        min_val = int(min_q.strip())
        max_val = int(max_q.strip())
    except ValueError:
        return await msg.answer("❌ Invalid format. Please send like: 10,10000")

    data = await state.get_data()
    
    db["smm_services"].update_one(
        {"_id": ObjectId(data["srv_id"])},
        {"$set": {
            "name": data["srv_name"],
            "price": data["srv_price"],
            "min": min_val,
            "max": max_val
        }}
    )
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🔙 Back to Admin", callback_data="smm_admin_main", icon_custom_emoji_id="5409284148491726576", style="danger"))
    await msg.answer(f"✅ <b>Service updated successfully!</b>\nName: {data['srv_name']}\nPrice: {fmt_curr(data['srv_price'])}\nLimits: {min_val} - {max_val}", parse_mode="HTML", reply_markup=kb.as_markup())
    await state.clear()


# --- REMOVE APP ---
@router.callback_query(F.data == "smm_rm_app")
async def rm_app_start(cq: CallbackQuery, db):
    apps = list(db["smm_apps"].find({}))
    if not apps:
        return await cq.answer("⚠️ No apps to remove!", show_alert=True)

    kb = InlineKeyboardBuilder()
    for app in apps:
        kb.row(InlineKeyboardButton(text=f"🗑️ {app['name']}", callback_data=f"smm_ra_sel:{str(app['_id'])}"))
    kb.row(InlineKeyboardButton(text="🔙 Back", callback_data="smm_admin_main", icon_custom_emoji_id="5409284148491726576", style="danger"))
    
    await cq.message.edit_text("🗑️ <b>Select the App you want to PERMANENTLY delete:</b>\n<i>(This will also delete all its services)</i>", parse_mode="HTML", reply_markup=kb.as_markup())
    await cq.answer()

@router.callback_query(F.data.startswith("smm_ra_sel:"))
async def rm_app_execute(cq: CallbackQuery, db):
    app_id = cq.data.split(":")[1]
    
    db["smm_apps"].delete_one({"_id": ObjectId(app_id)})
    db["smm_services"].delete_many({"app_id": app_id})
    
    await cq.answer("✅ App and all its services removed!", show_alert=True)
    await show_admin_panel(cq.message, db, edit_msg=True)

# --- REMOVE SERVICE ---
@router.callback_query(F.data == "smm_rm_service")
async def rm_srv_app_start(cq: CallbackQuery, db):
    apps = list(db["smm_apps"].find({}))
    if not apps:
        return await cq.answer("⚠️ No apps found!", show_alert=True)

    kb = InlineKeyboardBuilder()
    for app in apps:
        kb.row(InlineKeyboardButton(text=app["name"], callback_data=f"smm_rs_app:{str(app['_id'])}"))
    kb.row(InlineKeyboardButton(text="🔙 Back", callback_data="smm_admin_main", icon_custom_emoji_id="5409284148491726576", style="danger"))
    
    await cq.message.edit_text("📱 <b>Select the App containing the service to remove:</b>", parse_mode="HTML", reply_markup=kb.as_markup())
    await cq.answer()

@router.callback_query(F.data.startswith("smm_rs_app:"))
async def rm_srv_list(cq: CallbackQuery, db):
    app_id = cq.data.split(":")[1]
    services = list(db["smm_services"].find({"app_id": app_id}))
    
    if not services:
        return await cq.answer("⚠️ No services under this app!", show_alert=True)

    kb = InlineKeyboardBuilder()
    for srv in services:
        kb.row(InlineKeyboardButton(text=f"🗑️ {srv['name']} - {fmt_curr(srv['price'])}", callback_data=f"smm_rs_srv:{str(srv['_id'])}"))
    kb.row(InlineKeyboardButton(text="🔙 Back", callback_data="smm_rm_service", icon_custom_emoji_id="5409284148491726576", style="danger"))
    
    await cq.message.edit_text("🗑️ <b>Select the Service to PERMANENTLY Delete:</b>", parse_mode="HTML", reply_markup=kb.as_markup())
    await cq.answer()

@router.callback_query(F.data.startswith("smm_rs_srv:"))
async def rm_srv_execute(cq: CallbackQuery, db):
    srv_id = cq.data.split(":")[1]
    
    db["smm_services"].delete_one({"_id": ObjectId(srv_id)})
    
    await cq.answer("✅ Service removed successfully!", show_alert=True)
    await show_admin_panel(cq.message, db, edit_msg=True)

# ==========================================
#               USER PANEL
# ==========================================

@router.callback_query(F.data == "feature_smm_external")
async def ext_smm_main(cq: CallbackQuery, db):
    apps = list(db["smm_apps"].find({}))
    
    text = (
        f"<b>🌍 External SMM Services</b>\n"
        f"––––––—–————––––——–––•\n"
        f"<blockquote>• Top tier social media growth\n"
        f"• Instant start, high quality\n"
        f"• Automated processing via API</blockquote>\n\n"
        f"👇 <b>Select a platform to continue:</b>"
    )

    kb = InlineKeyboardBuilder()
    
    app_buttons = []
    for app in apps:
        kwargs = {"text": app["name"], "callback_data": f"ext_smm_app:{str(app['_id'])}"}
        if app.get("emoji_id"):
            kwargs["icon_custom_emoji_id"] = app["emoji_id"]
        app_buttons.append(InlineKeyboardButton(**kwargs))
    
    kb.add(*app_buttons)
    kb.adjust(2)
    
    kb.row(
        InlineKeyboardButton(text="Back", callback_data="back_main", icon_custom_emoji_id="5409284148491726576", style="danger"),
        InlineKeyboardButton(text="Search", callback_data="ext_smm_search", icon_custom_emoji_id="5429571366384842791", style="success")
    )
    kb.row(
        InlineKeyboardButton(text="📜 Purchase Logs", callback_data="ext_smm_history:0", style="success")
    )

    
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await cq.answer()

@router.callback_query(F.data == "ext_smm_search")
async def ext_smm_search_prompt(cq: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Back", callback_data="feature_smm_external", icon_custom_emoji_id="5409284148491726576", style="danger"))
    
    await cq.message.edit_text("🔍 <b>Send a keyword to search for a service:</b>\n<i>(e.g., 'Instagram', 'Likes', 'Views')</i>", parse_mode="HTML", reply_markup=kb.as_markup())
    await state.set_state(SMMUserState.waiting_search)
    await cq.answer()

@router.message(StateFilter(SMMUserState.waiting_search))
async def ext_smm_search_results(msg: Message, state: FSMContext, db):
    keyword = msg.text.strip().lower()
    
    services = list(db["smm_services"].find({"name": {"$regex": keyword, "$options": "i"}}).limit(15))
    
    if not services:
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="Back", callback_data="feature_smm_external", icon_custom_emoji_id="5409284148491726576", style="danger"))
        return await msg.answer("❌ <b>No services found.</b> Try another keyword.", parse_mode="HTML", reply_markup=kb.as_markup())

    text = f"🔍 <b>Search Results for '{keyword}':</b>\n––––––—–————––––——–––•\n"
    
    kb = InlineKeyboardBuilder()
    for srv in services:
        kb.row(InlineKeyboardButton(
            text=f"{srv['name']} - {fmt_curr(srv['price'])}",
            callback_data=f"ext_srv:{str(srv['_id'])}"
        ))
        
    kb.row(InlineKeyboardButton(text="Back to Apps", callback_data="feature_smm_external", icon_custom_emoji_id="5409284148491726576", style="danger"))
    
    await msg.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await state.clear()


@router.callback_query(F.data.startswith("ext_smm_app:"))
async def ext_smm_services(cq: CallbackQuery, db):
    parts = cq.data.split(":")
    app_id = parts[1]
    page = int(parts[2]) if len(parts) > 2 else 0
    limit = 10
    skip = page * limit

    services = list(db["smm_services"].find({"app_id": app_id}).skip(skip).limit(limit))
    total_services = db["smm_services"].count_documents({"app_id": app_id})

    app_doc = db["smm_apps"].find_one({"_id": ObjectId(app_id)})
    app_name = app_doc["name"] if app_doc else "Platform"

    text = (
        f"<b>📱 {app_name} Services</b>\n"
        f"––––––—–————––––——–––•\n"
        f"<i>Select a service from the list below:</i>\n"
    )

    kb = InlineKeyboardBuilder()
    for srv in services:
        kb.row(InlineKeyboardButton(
            text=f"{srv['name']} - {fmt_curr(srv['price'])}",
            callback_data=f"ext_srv:{str(srv['_id'])}"
        ))

    nav_btns = []
    if page > 0:
        nav_btns.append(InlineKeyboardButton(text="⬅️ Previous", callback_data=f"ext_smm_app:{app_id}:{page-1}"))
    if skip + limit < total_services:
        nav_btns.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"ext_smm_app:{app_id}:{page+1}"))
    
    if nav_btns:
        kb.row(*nav_btns)

    kb.row(InlineKeyboardButton(text="Back to Apps", callback_data="feature_smm_external", icon_custom_emoji_id="5409284148491726576", style="danger"))
    
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await cq.answer()

@router.callback_query(F.data.startswith("ext_srv:"))
async def ext_smm_service_details(cq: CallbackQuery, state: FSMContext, db):
    srv_id = cq.data.split(":")[1]
    srv = db["smm_services"].find_one({"_id": ObjectId(srv_id)})
    
    app = db["smm_apps"].find_one({"_id": ObjectId(srv['app_id'])})
    app_name = app["name"] if app else "Platform"

    text = (
        f"<b>🛒 SMM - Panel Order</b>\n"
        f"––––––—–————––––——–––•\n"
        f"<blockquote><b>📱 App:</b> {app_name}\n"
        f"<b>🏷️ Service:</b> {srv['name']}\n"
        f"<b>💰 Price:</b> {fmt_curr(srv['price'])} per 1000\n"
        f"<b>📊 Limits:</b> Min {srv['min']} / Max {srv['max']}</blockquote>\n\n"
        f"❓ <b>Are you sure you want to purchase this service?</b>"
    )

    await state.update_data(srv=srv, app_name=app_name)

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="✅ Confirm", callback_data="ext_srv_confirm", style="success"),
           InlineKeyboardButton(text="Cancel", callback_data=f"ext_smm_app:{srv['app_id']}", icon_custom_emoji_id="5409284148491726576", style="danger"))

    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await cq.answer()

@router.callback_query(F.data == "ext_srv_confirm")
async def ext_smm_confirm(cq: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Cancel", callback_data="feature_smm_external", icon_custom_emoji_id="5409284148491726576", style="danger"))
    await cq.message.edit_text("🔗 <b>Please send the target Link:</b>\n<i>(e.g., Profile URL, Post URL)</i>", parse_mode="HTML", reply_markup=kb.as_markup())
    await state.set_state(SMMUserState.waiting_link)
    await cq.answer()

@router.message(StateFilter(SMMUserState.waiting_link))
async def ext_smm_link(msg: Message, state: FSMContext):
    await state.update_data(link=msg.text.strip())
    data = await state.get_data()
    srv = data["srv"]
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Cancel", callback_data="feature_smm_external", icon_custom_emoji_id="5409284148491726576", style="danger"))
    await msg.answer(f"🔢 <b>Enter Quantity:</b>\n<i>(Min: {srv['min']} | Max: {srv['max']})</i>", parse_mode="HTML", reply_markup=kb.as_markup())
    await state.set_state(SMMUserState.waiting_quantity)

@router.message(StateFilter(SMMUserState.waiting_quantity))
async def ext_smm_quantity(msg: Message, state: FSMContext):
    try:
        qty = int(msg.text.strip())
    except ValueError:
        return await msg.answer("❌ Invalid number. Please enter a valid quantity.")

    data = await state.get_data()
    srv = data["srv"]
    
    if qty < srv["min"] or qty > srv["max"]:
        return await msg.answer(f"❌ Quantity out of limits ({srv['min']} - {srv['max']}). Please try again.")

    total_price = (qty / 1000) * srv["price"]
    await state.update_data(qty=qty, total_price=total_price)

    text = (
        f"<b>📝 Order Overview</b>\n"
        f"––––––—–————––––——–––•\n"
        f"<blockquote><b>🏷️ Service:</b> {srv['name']}\n"
        f"<b>🔗 Link:</b> {data['link']}\n"
        f"<b>🔢 Quantity:</b> {qty}\n"
        f"<b>💰 Total Cost:</b> {fmt_curr(total_price)}</blockquote>\n\n"
        f"👇 Click below to complete your order."
    )

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="💸 Buy Now", callback_data="ext_srv_buy", style="success"))
    kb.row(InlineKeyboardButton(text="Cancel Order", callback_data="feature_smm_external", icon_custom_emoji_id="5409284148491726576", style="danger"))

    await msg.answer(text, parse_mode="HTML", disable_web_page_preview=True, reply_markup=kb.as_markup())

@router.callback_query(F.data == "ext_srv_buy")
async def ext_smm_terms(cq: CallbackQuery):
    text = (
        f"<b>⚠️ Purchasing Terms</b>\n"
        f"––––––—–————––––——–––•\n"
        f"<blockquote>• Orders are non-refundable once placed.\n"
        f"• Ensure your profile/link is PUBLIC.\n"
        f"• Do not place multiple orders for the same link concurrently.</blockquote>\n\n"
        f"<i>Do you accept these terms?</i>"
    )
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="✅ Accept & Purchase", callback_data="ext_srv_execute", style="success"),
           InlineKeyboardButton(text="Decline", callback_data="feature_smm_external", icon_custom_emoji_id="5409284148491726576", style="danger"))
    
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await cq.answer()

@router.callback_query(F.data == "ext_srv_execute")
async def ext_smm_execute(cq: CallbackQuery, state: FSMContext, db):
    user_id = cq.from_user.id
    now = time.time()

    # 3-Second Freeze Anti-Spam
    if user_id in click_cache and now - click_cache[user_id] < 3:
        return await cq.answer("❄️ Please wait 3 seconds before clicking again.", show_alert=True)
    click_cache[user_id] = now

    data = await state.get_data()
    total_price = data["total_price"]
    app_name = data.get("app_name", "Platform")
    
    user = db["users"].find_one({"_id": user_id})
    if user.get("balance", 0) < total_price:
        return await cq.answer("❌ Insufficient balance. Please recharge.", show_alert=True)

    status_msg = await cq.message.edit_text("🔄 <i>Placing order on SMM Panel...</i>", parse_mode="HTML")

    # API Call
    resp = await call_api("add", service=data['srv']['service_id'], link=data['link'], quantity=data['qty'])

    if "order" in resp:
        # Success
        order_id = resp["order"]
        db["users"].update_one({"_id": user_id}, {"$inc": {"balance": -total_price}})
        
        # Save to DB
        db["smm_orders"].insert_one({
            "user_id": user_id,
            "order_id": order_id,
            "service": data['srv']['name'],
            "link": data['link'],
            "qty": data['qty'],
            "cost": total_price,
            "date": datetime.now(timezone.utc)
        })

        success_text = (
            f"<b>✅ Order Confirmed!</b>\n"
            f"––––––—–————––––——–––•\n"
            f"<blockquote><b>🆔 Order ID:</b> <code>{order_id}</code>\n"
            f"<b>🏷️ Service:</b> {data['srv']['name']}\n"
            f"<b>🔢 Qty:</b> {data['qty']}\n"
            f"<b>💸 Paid:</b> {fmt_curr(total_price)}</blockquote>\n\n"
            f"⚠️ <b>Note:</b> <i>Some services may take time to reflect, get processing, or show status updates inside the bot due to global server latency. Please be patient.</i>"
        )

        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="🔍 Check Status", callback_data=f"ext_smm_status:{order_id}", style="success"))
        

        await status_msg.edit_text(success_text, parse_mode="HTML", reply_markup=kb.as_markup())

        # Notify Admin Channel
        admin_log = (
            f"<b>🚀 New External SMM Order</b>\n"
            f"👤 User: <code>{user_id}</code>\n"
            f"🆔 API Order: <code>{order_id}</code>\n"
            f"🏷️ Srv: {data['srv']['name']} (ID: {data['srv']['service_id']})\n"
            f"🔢 Qty: {data['qty']}\n"
            f"💰 Cost: {fmt_curr(total_price)}"
        )
        try:
            await cq.bot.send_message(-1003208353049, admin_log, parse_mode="HTML")
        except: 
            pass

        # === PUBLIC SALES LOG ===
        public_log_text = (
            f"<pre>✅ New SMM purchase completed</pre>\n\n"
            f"<b>➕ Application -</b> {app_name}\n"
            f"<b>🏷️ Service -</b> {data['srv']['name']}\n"
            f"<b>👤 User -</b> <code>{mask_user_id(user_id)}</code>\n\n"
            f"<b>💰 Paid amount -</b> {fmt_curr(total_price)}\n"
            f"<blockquote>• @Tgbitz || @Tgbitz_bot</blockquote>"
        )
        
        public_kb = InlineKeyboardBuilder()
        public_kb.row(InlineKeyboardButton(
            text="Order Now", 
            url="https://t.me/Tgbitz_bot?start=starting", style="success"
        ))

        try:
            await cq.bot.send_message(
                chat_id=-1004484806488, 
                text=public_log_text, 
                parse_mode="HTML", 
                reply_markup=public_kb.as_markup()
            )
        except Exception as e: 
            print(f"Failed to send public log: {e}")

    else:
        # Panel Error / Balance Issue
        error_msg = resp.get('error', 'Unknown Error')
        await status_msg.edit_text(f"❌ <b>Order Failed:</b> {error_msg}\n<i>No balance was deducted.</i>", parse_mode="HTML")
        
        try:
            await cq.bot.send_message(-1004492615113, f"⚠️ <b>PANEL ERROR:</b>\nFailed to place order for User <code>{user_id}</code>.\nReason: {error_msg}", parse_mode="HTML")
        except: 
            pass

    await state.clear()


@router.callback_query(F.data.startswith("ext_smm_status:"))
async def ext_smm_status(cq: CallbackQuery, state: FSMContext):
    order_id = cq.data.split(":")[1]
    
    resp = await call_api("status", order=order_id)
    
    if "error" in resp:
        return await cq.answer(f"❌ Error: {resp['error']}", show_alert=True)
    
    # Process properties cleanly from API payload
    status = str(resp.get("status", "Unknown")).title()
    start_count = str(resp.get("start_count", "")).strip()
    remains = resp.get("remains", "N/A")
    
    if not start_count:
        start_count = "0"
    
    status_emoji = "⏳"
    if status.lower() == "completed":
        status_emoji = "✅"
    elif status.lower() in ["canceled", "cancelled", "refunded"]:
        status_emoji = "❌"
    elif status.lower() in ["processing", "in progress"]:
        status_emoji = "🔄"

    # Present alert popup configuration requested
    alert_text = f"📌 Status: {status}\n📈 Start Count: {start_count}"
    
    text = (
        f"<b>🔍 Order Status (ID: <code>{order_id}</code>)</b>\n"
        f"––––––—–————––––——–––•\n"
        f"<blockquote><b>📌 Status:</b> {status_emoji} {status}\n"
        f"<b>📈 Start Count:</b> {start_count}\n"
        f"<b>⏳ Remains:</b> {remains}</blockquote>\n"
        f"⚠️ <b>Note:</b> <i>Some services may take time to reflect, get processing, or show status updates inside the bot due to global server latency. Please be patient.</i>"
    
    )
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🔄 Refresh", callback_data=cq.data, style="success"))
    
    try:
        await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    except:
        pass 
        
    # Trigger alert popup box for the user
    await cq.answer(text=alert_text, show_alert=True)
@router.callback_query(F.data.startswith("ext_smm_history:"))
async def ext_smm_history(cq: CallbackQuery, db):
    user_id = cq.from_user.id
    page = int(cq.data.split(":")[1])
    limit = 10
    skip = page * limit
    
    # Query database and sort by newest
    cursor = db["smm_orders"].find({"user_id": user_id}).sort("date", -1)
    total_orders = db["smm_orders"].count_documents({"user_id": user_id})
    orders = list(cursor.skip(skip).limit(limit))
    
    if not orders:
        return await cq.answer("❌ No SMM purchase history found.", show_alert=True)
        
    text = f"📜 <b>Your SMM Purchase Logs (Page {page+1})</b>\n––––––—–————––––——–––•\n"
    
    for o in orders:
        date_str = o["date"].strftime("%Y-%m-%d %H:%M") if "date" in o else "Unknown"
        text += (
            f"🏷️ <b>{o.get('service', 'Unknown')}</b>\n"
            f"🔢 Amount: <code>{o.get('qty', 0)}</code> | 💰 Price: <code>{fmt_curr(o.get('cost', 0))}</code>\n"
            f"📅 Date: <i>{date_str}</i>\n"
            f"–––––––––––––––––––––––\n"
        )
        
    kb = InlineKeyboardBuilder()
    nav_btns = []
    
    if page > 0:
        nav_btns.append(InlineKeyboardButton(text="⬅️ Previous", callback_data=f"ext_smm_history:{page-1}"))
    if skip + limit < total_orders:
        nav_btns.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"ext_smm_history:{page+1}"))
        
    if nav_btns:
        kb.row(*nav_btns)
        
    kb.row(InlineKeyboardButton(text="Back", callback_data="feature_smm_external", style="danger"))
    
    await cq.message.edit_text(text, parse_mode="HTML", disable_web_page_preview=True, reply_markup=kb.as_markup())
    await cq.answer()
    
# Register external SMM handlers hook
def register_smmpanel_handlers(dp, db):
    dp.include_router(router)
