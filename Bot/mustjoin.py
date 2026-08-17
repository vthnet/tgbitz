from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import MUST_JOIN_CHANNEL

# Private channel details
PRIVATE_CHANNEL_ID = -1004361894565
PRIVATE_CHANNEL_LINK = "https://t.me/+KGRCv3PD9n4xZWNk"
PRIVATE_CHANNEL_ID2 = -1004484806488

BOTUSER = "tgbitz_bot"
# Welcome text with HTML formatting
WELCOME_TEXT = ('<tg-emoji emoji-id="6129579803600231171">❌</tg-emoji><b> Welcome to Tgbitz_bot by TGbitz </b>\n\n<tg-emoji emoji-id="5902362294041448273">❌</tg-emoji> <b><i>𝖸𝗈𝗎 𝗆𝗎𝗌𝗍 join 𝗍𝗁𝖾 𝗈𝖿𝖿𝗂𝖼𝗂𝖺𝗅 𝖻𝗈𝗍 𝖼𝗁𝖺𝗇𝗇𝖾𝗅s first 𝗍𝗈 𝗎𝗌𝖾 𝗍𝗁𝖾 𝖻𝗈𝗍 .</i></b>\n<blockquote><tg-emoji emoji-id="5909174430000484676">❌</tg-emoji> click on the support and updates buttons below to join the channels</blockquote>\n<blockquote><tg-emoji emoji-id="5899791674510414549">❌</tg-emoji> Press Verify Button below after joining.</blockquote>\n• <b>Support : @ogbitz</b>')



async def check_join(client, message: types.Message):
    """
    Check if the user has joined both required channels.
    If not, send the join message and return False.~
    """
    try:
        # Public channel check
        member1 = await client.get_chat_member(PRIVATE_CHANNEL_ID2, message.from_user.id)

        # Private channel check
        member2 = await client.get_chat_member(PRIVATE_CHANNEL_ID, message.from_user.id)

        if (member1.status in ["left", "kicked"]) or (member2.status in ["left", "kicked"]):
            await send_join_message(message)
            return False

        return True
    except Exception:
        await send_join_message(message)
        return False


async def send_join_message(message: types.Message):
    """
    Send a message asking the user to join the required channels,
    with inline buttons for both channels in one row and Verify below.
    """
    kb = InlineKeyboardBuilder()

    # First row: both channels
    kb.row(
        types.InlineKeyboardButton(text="𝖴𝗉𝖽𝖺𝗍𝖾𝗌", url=f"https://t.me/tgbitz", style="danger", icon_custom_emoji_id="5215668805199473901"),
        types.InlineKeyboardButton(text="𝖲𝗎𝗉𝗉𝗈𝗋𝗍 ", url="https://t.me/tgbitz_log", style="danger", icon_custom_emoji_id="5409132617750555920")
    )
    kb.row(
         types.InlineKeyboardButton(text="Verify Join", callback_data="back_main", style="success", icon_custom_emoji_id="5408955961450705923")
    )
        

    

    await message.answer(
        WELCOME_TEXT,
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )
