import asyncio
from datetime import datetime, timezone
from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command, StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bson.objectid import ObjectId

# ================= FSM States =================
class AddSrcFSM(StatesGroup):
    waiting_name = State()
    waiting_zip = State()
    waiting_price = State()
    waiting_desc = State()

class AddPanelFSM(StatesGroup):
    waiting_name = State()
    waiting_link = State()
    waiting_price = State()
    waiting_desc = State()

# ================= MAIN REGISTRATION FUNCTION =================
def register_buysrc_panels_handlers(dp, bot, db, users_col, is_admin_func, fmt_curr_func):
    
    # Initialize Collections
    src_col = db["source_codes"]
    panels_col = db["panels"]
    
    # Log Channels
    SALESLOG = "-1004484806488"
    ADMINLOG = "-1004492615113"

    # ================= ADMIN COMMANDS: SOURCE CODES =================

    @dp.message(Command("addsrc", "addsrcname"))
    async def cmd_add_src(msg: Message, state: FSMContext):
        if not is_admin_func(msg.from_user.id): return
        await msg.answer("📦 <b>Add New Source Code</b>\n\nPlease enter the NAME of the source code:")
        await state.set_state(AddSrcFSM.waiting_name)

    @dp.message(StateFilter(AddSrcFSM.waiting_name))
    async def process_src_name(msg: Message, state: FSMContext):
        await state.update_data(name=msg.text)
        await msg.answer("📂 Please send the <b>.zip</b> file of the source code:")
        await state.set_state(AddSrcFSM.waiting_zip)

    @dp.message(StateFilter(AddSrcFSM.waiting_zip), F.document)
    async def process_src_zip(msg: Message, state: FSMContext):
        if not msg.document.file_name.endswith('.zip'):
            return await msg.answer("❌ Please upload a valid .zip file.")
        
        await state.update_data(file_id=msg.document.file_id)
        await msg.answer("💰 Enter the <b>Price in INR</b> (e.g. 500):")
        await state.set_state(AddSrcFSM.waiting_price)

    @dp.message(StateFilter(AddSrcFSM.waiting_price))
    async def process_src_price(msg: Message, state: FSMContext):
        try:
            price = float(msg.text)
            await state.update_data(price=price)
            await msg.answer("📝 Enter a description for this source code:")
            await state.set_state(AddSrcFSM.waiting_desc)
        except ValueError:
            await msg.answer("❌ Invalid price. Please enter a number.")

    @dp.message(StateFilter(AddSrcFSM.waiting_desc))
    async def process_src_desc(msg: Message, state: FSMContext):
        data = await state.get_data()
        src_col.insert_one({
            "name": data["name"],
            "file_id": data["file_id"],
            "price": data["price"],
            "desc": msg.text,
            "added_at": datetime.now(timezone.utc)
        })
        await msg.answer(f"✅ <b>Source Code Added!</b>\nName: {data['name']}\nPrice: ₹{data['price']}", parse_mode="HTML")
        await state.clear()

    @dp.message(Command("removesrc", "removesrcname"))
    async def cmd_remove_src(msg: Message):
        if not is_admin_func(msg.from_user.id): return
        sources = list(src_col.find({}))
        if not sources:
            return await msg.answer("❌ No source codes available.")
        
        kb = InlineKeyboardBuilder()
        for s in sources:
            kb.button(text=f"❌ {s['name']}", callback_data=f"delsrc:{s['_id']}")
        kb.adjust(1)
        await msg.answer("🗑️ <b>Select a source code to delete:</b>", reply_markup=kb.as_markup(), parse_mode="HTML")

    @dp.callback_query(F.data.startswith("delsrc:"))
    async def process_del_src(cq: CallbackQuery):
        if not is_admin_func(cq.from_user.id): return
        src_id = cq.data.split(":")[1]
        src_col.delete_one({"_id": ObjectId(src_id)})
        await cq.message.edit_text("✅ Source code deleted.")
        await cq.answer()


    # ================= ADMIN COMMANDS: PANELS =================

    @dp.message(Command("addpanel", "addpanelname"))
    async def cmd_add_panel(msg: Message, state: FSMContext):
        if not is_admin_func(msg.from_user.id): return
        await msg.answer("🖥️ <b>Add New Panel</b>\n\nPlease enter the NAME of the panel:")
        await state.set_state(AddPanelFSM.waiting_name)

    @dp.message(StateFilter(AddPanelFSM.waiting_name))
    async def process_panel_name(msg: Message, state: FSMContext):
        await state.update_data(name=msg.text)
        await msg.answer("🔗 Please send the <b>Direct Link</b> for the panel:")
        await state.set_state(AddPanelFSM.waiting_link)

    @dp.message(StateFilter(AddPanelFSM.waiting_link))
    async def process_panel_link(msg: Message, state: FSMContext):
        await state.update_data(link=msg.text)
        await msg.answer("💰 Enter the <b>Price in INR</b> (e.g. 500):")
        await state.set_state(AddPanelFSM.waiting_price)

    @dp.message(StateFilter(AddPanelFSM.waiting_price))
    async def process_panel_price(msg: Message, state: FSMContext):
        try:
            price = float(msg.text)
            await state.update_data(price=price)
            await msg.answer("📝 Enter a description for this panel:")
            await state.set_state(AddPanelFSM.waiting_desc)
        except ValueError:
            await msg.answer("❌ Invalid price. Please enter a number.")

    @dp.message(StateFilter(AddPanelFSM.waiting_desc))
    async def process_panel_desc(msg: Message, state: FSMContext):
        data = await state.get_data()
        panels_col.insert_one({
            "name": data["name"],
            "link": data["link"],
            "price": data["price"],
            "desc": msg.text,
            "added_at": datetime.now(timezone.utc)
        })
        await msg.answer(f"✅ <b>Panel Added!</b>\nName: {data['name']}\nPrice: ₹{data['price']}", parse_mode="HTML")
        await state.clear()

    @dp.message(Command("removepanel"))
    async def cmd_remove_panel(msg: Message):
        if not is_admin_func(msg.from_user.id): return
        panels = list(panels_col.find({}))
        if not panels:
            return await msg.answer("❌ No panels available.")
        
        kb = InlineKeyboardBuilder()
        for p in panels:
            kb.button(text=f"❌ {p['name']}", callback_data=f"delpanel:{p['_id']}")
        kb.adjust(1)
        await msg.answer("🗑️ <b>Select a panel to delete:</b>", reply_markup=kb.as_markup(), parse_mode="HTML")

    @dp.callback_query(F.data.startswith("delpanel:"))
    async def process_del_panel(cq: CallbackQuery):
        if not is_admin_func(cq.from_user.id): return
        panel_id = cq.data.split(":")[1]
        panels_col.delete_one({"_id": ObjectId(panel_id)})
        await cq.message.edit_text("✅ Panel deleted.")
        await cq.answer()


    # ================= USER FLOW: BUY SOURCE CODE =================

    @dp.callback_query(F.data == "buy_src_menu")
    async def user_buy_src_menu(cq: CallbackQuery):
        sources = list(src_col.find({}))
        kb = InlineKeyboardBuilder()
        
        for s in sources:
            kb.button(text=f"{s['name']} - ₹{s['price']}", callback_data=f"usrc_sel:{s['_id']}")
        kb.adjust(1)
        kb.row(InlineKeyboardButton(text="Back", callback_data="back_main", icon_custom_emoji_id="5409284148491726576", style="danger"))

        text = (
            "💻 <b>Tgbitz Src Panel</b>\n"
            "––––––—–————––––——–––•\n"
            "• Readymade codes, Create your own bots\n"
            "• All things are done already you just have to edit the details\n\n"
            "<i>Select the source code you wanna buy:</i>"
        )
        await cq.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
        await cq.answer()

    @dp.callback_query(F.data.startswith("usrc_sel:"))
    async def user_src_selected(cq: CallbackQuery):
        src_id = cq.data.split(":")[1]
        src = src_col.find_one({"_id": ObjectId(src_id)})
        user = users_col.find_one({"_id": cq.from_user.id})
        balance = user.get("balance", 0.0)

        if not src:
            return await cq.answer("❌ Source code no longer available.", show_alert=True)

        text = (
            f"🛒 <b>Source Code Purchase</b>\n"
            f"––––––—–————––––——–––•\n"
            f"📝 <b>You selected:</b> {src['name']}\n"
            f"💵 <b>Price:</b> ₹{src['price']}\n"
            f"💰 <b>Your balance:</b> ₹{balance}\n"
            f"📄 <b>Description:</b>\n<blockquote expandable>{src['desc']}</blockquote>"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Buy Now", callback_data=f"usrc_buy:{src_id}", style="success")],
            [InlineKeyboardButton(text="❌ Cancel and back", callback_data="buy_src_menu", style="danger")]
        ])
        await cq.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await cq.answer()

    @dp.callback_query(F.data.startswith("usrc_buy:"))
    async def user_src_buy_check(cq: CallbackQuery):
        src_id = cq.data.split(":")[1]
        src = src_col.find_one({"_id": ObjectId(src_id)})
        user = users_col.find_one({"_id": cq.from_user.id})
        
        if user.get("balance", 0.0) < src['price']:
            return await cq.answer("❌ Insufficient balance! Please top-up.", show_alert=True)

        terms_text = (
            "⚠️ <b>Terms and Conditions</b>\n"
            "––––––—–————––––——–––•\n"
            "• Remember these source codes are up to date\n"
            "• <b><u>Hosting</u></b>- can be hosted on Heroku & VPS\n"
            "• <b><u>Database</u></b> - MongoDB Atlas\n\n"
            "<i>The source code once purchased is non-refundable.</i>"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Accept and buy", callback_data=f"usrc_accept:{src_id}", style="success")],
            [InlineKeyboardButton(text="❌ Decline and back", callback_data="buy_src_menu", style="danger")]
        ])
        await cq.message.edit_text(terms_text, reply_markup=kb, parse_mode="HTML")
        await cq.answer()

    @dp.callback_query(F.data.startswith("usrc_accept:"))
    async def user_src_process_purchase(cq: CallbackQuery):
        src_id = cq.data.split(":")[1]
        src = src_col.find_one({"_id": ObjectId(src_id)})
        user_id = cq.from_user.id
        user = users_col.find_one({"_id": user_id})

        if user.get("balance", 0.0) < src['price']:
            return await cq.answer("❌ Insufficient balance!", show_alert=True)

        users_col.update_one({"_id": user_id}, {"$inc": {"balance": -src['price']}})
        
        await cq.message.edit_text("⏳ <i>Preparing zip for you...</i>", parse_mode="HTML")
        
        caption = (
            f"📦 <b>{src['name']}</b>\n\n"
            f"⚠️ <i>This zip will be deleted in 10 minutes, so please forward this to Saved Messages. For more details DM support.</i>\n"
            f"📝 <b>Details:</b>\n<blockquote expandable> {src['desc']}</blockquote>"
        )

        try:
            sent_msg = await bot.send_document(
                chat_id=user_id,
                document=src['file_id'],
                caption=caption,
                parse_mode="HTML"
            )
            await cq.message.delete()
            
            # Format Masked ID
            masked_id = str(user_id)[:5] + "****"

            # Admin & Sales Logs
            log_msg = (
                f"<pre><b>✅ New source code purchase</b></pre>\n\n"
                f"➕ <b><u>Src</u>-</b> {src['name']}\n"
                f"➕ <b><u>Price</u> -</b> ₹{src['price']}\n"
                f"➕ <b><u>Type</u> -</b> .zip\n\n"
                f"🍷 <b><u>Buyer</u> -</b> {masked_id}\n"
                f"🥂 <b><u>Server</u> -</b> Panel/src market\n\n"
                f"• @tgbitz || @tgbitz_bot"
            )
            
            buy_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Buy now", url="https://t.me/tgbitz_bot?start=starting", style="success")]
            ])

            await bot.send_message(SALESLOG, log_msg, parse_mode="HTML", reply_markup=buy_kb)
            await bot.send_message(ADMINLOG, log_msg, parse_mode="HTML", reply_markup=buy_kb)

            # Auto-delete schedule
            await asyncio.sleep(600)
            try:
                await sent_msg.delete()
            except:
                pass
                
        except Exception as e:
            await cq.message.edit_text(f"❌ Failed to send file. Contact admin.\nError: {e}", parse_mode="HTML")


    # ================= USER FLOW: BUY PANELS =================

    @dp.callback_query(F.data == "buy_panel_menu")
    async def user_buy_panel_menu(cq: CallbackQuery):
        panels = list(panels_col.find({}))
        kb = InlineKeyboardBuilder()
        
        for p in panels:
            kb.button(text=f"{p['name']} - ₹{p['price']}", callback_data=f"upanel_sel:{p['_id']}")
        kb.adjust(1)
        kb.row(InlineKeyboardButton(text="Back", callback_data="back_main", icon_custom_emoji_id="5409284148491726576", style="danger"))

        text = (
            "🌌 <b>Tgbitz Panel Store</b>\n"
            "––––––—–————––––——–––•\n• Cheapest and Trusted panels\n• These panels are used by us also\n\n"
            "<i>Select the panel you wanna buy:</i>"
        )
        await cq.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
        await cq.answer()

    @dp.callback_query(F.data.startswith("upanel_sel:"))
    async def user_panel_selected(cq: CallbackQuery):
        panel_id = cq.data.split(":")[1]
        panel = panels_col.find_one({"_id": ObjectId(panel_id)})
        user = users_col.find_one({"_id": cq.from_user.id})
        
        if not panel:
            return await cq.answer("❌ Panel no longer available.", show_alert=True)

        text = (
            f"🛒 <b>Panel Purchase</b>\n"
            f"––––––—–————––––——–––•\n"
            f"📝 <b>You selected:</b> {panel['name']}\n"
            f"💵 <b>Price:</b> ₹{panel['price']}\n"
            f"💰 <b>Your balance:</b> ₹{user.get('balance', 0.0)}\n"
            f"📄 <b>Description:</b> \n<blockquote expandable>{panel['desc']}</blockquote>"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Buy Now", callback_data=f"upanel_buy:{panel_id}", style="success")],
            [InlineKeyboardButton(text="❌ Cancel and back", callback_data="buy_panel_menu", style="danger")]
        ])
        await cq.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await cq.answer()

    @dp.callback_query(F.data.startswith("upanel_buy:"))
    async def user_panel_buy_check(cq: CallbackQuery):
        panel_id = cq.data.split(":")[1]
        panel = panels_col.find_one({"_id": ObjectId(panel_id)})
        user = users_col.find_one({"_id": cq.from_user.id})
        
        if user.get("balance", 0.0) < panel['price']:
            return await cq.answer("❌ Insufficient balance! Please top-up.", show_alert=True)

        terms_text = (
            "⚠️ <b>Terms and Conditions</b>\n"
            "––––––—–————––––——–––•\n"
            "• Premium high-quality panels\n"
            "• Delivered via direct secured link instantly\n\n"
            "<i>The panel link once purchased is non-refundable.</i>"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Accept and buy", callback_data=f"upanel_accept:{panel_id}", style="success")],
            [InlineKeyboardButton(text="❌ Decline and back", callback_data="buy_panel_menu", style="danger")]
        ])
        await cq.message.edit_text(terms_text, reply_markup=kb, parse_mode="HTML")
        await cq.answer()

    @dp.callback_query(F.data.startswith("upanel_accept:"))
    async def user_panel_process_purchase(cq: CallbackQuery):
        panel_id = cq.data.split(":")[1]
        panel = panels_col.find_one({"_id": ObjectId(panel_id)})
        user_id = cq.from_user.id
        user = users_col.find_one({"_id": user_id})

        if user.get("balance", 0.0) < panel['price']:
            return await cq.answer("❌ Insufficient balance!", show_alert=True)

        users_col.update_one({"_id": user_id}, {"$inc": {"balance": -panel['price']}})
        
        await cq.message.edit_text("⏳ <i>Preparing link for you...</i>", parse_mode="HTML")
        
        caption = (
            f"🔗 <b>{panel['name']} Access</b>\n\n"
            f"🌐 <b>Panel Link:</b> {panel['link']}\n\n"
            f"⚠️ <i>This message will be deleted in 10 minutes, so please save the link immediately.</i>\n"
            f"📝 <b>Details:</b> \n<blockquote expandable>{panel['desc']}</blockquote>\n"
        )

        try:
            sent_msg = await bot.send_message(
                chat_id=user_id, 
                text=caption, 
                parse_mode="HTML",
                link_preview_options=LinkPreviewOptions(is_disabled=True)
            )
            await cq.message.delete()
            
            # Format Masked ID
            masked_id = str(user_id)[:5] + "****"

            # Admin & Sales Logs
            log_msg = (
                f"<pre><b>✅ New Panel purchase</b></pre>\n\n"
                f"➕ <b><u>panel</u> -</b> {panel['name']}\n"
                f"➕ <b><u>Price</u> -</b> ₹{panel['price']}\n"
                f"➕ <b><u>Type</u> -</b> Link\n\n"
                f"🍷 <b><u>Buyer</u>-</b> {masked_id}\n"
                f"🥂 <b><u>Server</u> -</b> Panel/src market\n\n"
                f"• @tgbitz || @tgbitz_bot"
            )
            
            buy_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Buy now", url="https://t.me/tgbitz_bot?start=starting", style="success")]
            ])

            await bot.send_message(SALESLOG, log_msg, parse_mode="HTML", reply_markup=buy_kb)
            await bot.send_message(ADMINLOG, log_msg, parse_mode="HTML", reply_markup=buy_kb)

            # Auto-delete schedule
            await asyncio.sleep(600)
            try:
                await sent_msg.delete()
            except:
                pass
                
        except Exception as e:
            await cq.message.edit_text(f"❌ Failed to send link. Contact admin.\nError: {e}", parse_mode="HTML")
