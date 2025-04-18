from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from itertools import groupby
import math
from html import escape
import random

from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import collection, user_collection, application

async def harem(update: Update, context: CallbackContext, page=0) -> None:
    user_id = update.effective_user.id
    user = await user_collection.find_one({'id': user_id})

    if not user:
        message = "You haven't collected any characters yet!"
        if update.message:
            await update.message.reply_text(message)
        else:
            await update.callback_query.edit_message_text(message)
        return

    characters = sorted(user['characters'], key=lambda x: (x['anime'], x['id']))
    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}
    unique_characters = list({character['id']: character for character in characters}.values())
    total_pages = math.ceil(len(unique_characters) / 15)

    page = max(0, min(page, total_pages - 1))  # Clamp page within range
    current_characters = unique_characters[page * 15:(page + 1) * 15]
    grouped = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])}

    # Header with decorative symbols
    harem_message = (
        f"<b>{escape(update.effective_user.first_name)}'s Harem</b>\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"<i>Page {page + 1} of {total_pages}</i>\n"
        f"ㅑㅑㅑㅑㅑㅑㅑㅑㅑㅑ\n"
    )

    # Characters grouped by anime
    for anime, chars in grouped.items():
        total_anime_chars = await collection.count_documents({"anime": anime})
        harem_message += f"\n<b>{escape(anime)}:</b> {len(chars)}/{total_anime_chars}\n"
        for char in chars:
            count = character_counts[char['id']]
            harem_message += f"  ➾ <code>{char['id']}</code> {escape(char['name'])} ×{count}\n"

    total_collected = len(user['characters'])

    # Buttons
    keyboard = [[
        InlineKeyboardButton(f"📜 View Full Collection ({total_collected})", switch_inline_query_current_chat=f"collection.{user_id}")
    ]]

    nav_buttons = []
    if total_pages > 1:
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"harem:{page - 1}:{user_id}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("Next ➾", callback_data=f"harem:{page + 1}:{user_id}"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Show image: favorite or random
    character_to_display = None
    if 'favorites' in user and user['favorites']:
        character_to_display = next((c for c in user['characters'] if c['id'] == user['favorites'][0]), None)
    if not character_to_display and user['characters']:
        character_to_display = random.choice(user['characters'])

    if character_to_display and 'img_url' in character_to_display:
        if update.message:
            await update.message.reply_photo(photo=character_to_display['img_url'], caption=harem_message, parse_mode='HTML', reply_markup=reply_markup)
        else:
            if update.callback_query.message.caption != harem_message:
                await update.callback_query.edit_message_caption(caption=harem_message, parse_mode='HTML', reply_markup=reply_markup)
    else:
        if update.message:
            await update.message.reply_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
        else:
            if update.callback_query.message.text != harem_message:
                await update.callback_query.edit_message_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)


async def harem_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    _, page, user_id = query.data.split(':')

    page = int(page)
    user_id = int(user_id)

    if query.from_user.id != user_id:
        await query.answer("This isn't your harem.", show_alert=True)
        return

    await harem(update, context, page)

# Handlers
application.add_handler(CommandHandler(["harem", "collection"], harem, block=False))
application.add_handler(CallbackQueryHandler(harem_callback, pattern='^harem', block=False))
