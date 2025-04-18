import os
import random
import html

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from shivu import (
    application, PHOTO_URL, OWNER_ID,
    user_collection, top_global_groups_collection,
    group_user_totals_collection, sudo_users as SUDO_USERS
)


async def global_leaderboard(update: Update, context: CallbackContext) -> None:
    cursor = top_global_groups_collection.aggregate([
        {"$project": {"group_name": 1, "count": 1}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = (
        "<b>‣ TOP 10 GROUPS WITH THE HIGHEST CHARACTER GUESSES</b>\n"
        "<i>(Across all groups globally)</i>\n\n"
    )

    for i, group in enumerate(leaderboard_data, start=1):
        group_name = html.escape(group.get('group_name', 'Unknown'))
        if len(group_name) > 15:
            group_name = group_name[:15] + '...'
        count = group['count']
        leaderboard_message += f"{i}. <b>{group_name}</b> ➜ <b>{count} guesses</b>\n"

    photo_url = random.choice(PHOTO_URL)
    await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')


async def ctop(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    cursor = group_user_totals_collection.aggregate([
        {"$match": {"group_id": chat_id}},
        {"$project": {"username": 1, "first_name": 1, "character_count": "$count"}},
        {"$sort": {"character_count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = (
        "<b>‣ TOP 10 USERS IN THIS GROUP</b>\n"
        "<i>(Based on the number of character guesses made)</i>\n\n"
    )

    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username', 'Unknown')
        first_name = html.escape(user.get('first_name', 'Unknown'))
        if len(first_name) > 15:
            first_name = first_name[:15] + '...'
        count = user['character_count']
        leaderboard_message += (
            f"{i}. <a href=\"https://t.me/{username}\"><b>{first_name}</b></a> ➜ <b>{count} guesses</b>\n"
        )

    photo_url = random.choice(PHOTO_URL)
    await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')


async def leaderboard(update: Update, context: CallbackContext) -> None:
    cursor = user_collection.aggregate([
        {"$project": {"username": 1, "first_name": 1, "character_count": {"$size": "$characters"}}},
        {"$sort": {"character_count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = (
        "<b>‣ TOP 10 USERS WORLDWIDE</b>\n"
        "<i>(Based on character collections across all games)</i>\n\n"
    )

    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username', 'Unknown')
        first_name = html.escape(user.get('first_name', 'Unknown'))
        if len(first_name) > 15:
            first_name = first_name[:15] + '...'
        character_count = user['character_count']
        leaderboard_message += (
            f"{i}. <a href=\"https://t.me/{username}\"><b>{first_name}</b></a> ➜ <b>{character_count} characters</b>\n"
        )

    photo_url = random.choice(PHOTO_URL)
    await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')


async def stats(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    user_count = await user_collection.count_documents({})
    group_ids = await group_user_totals_collection.distinct('group_id')

    await update.message.reply_text(
        f"<b>System Summary:</b>\n"
        f"‣ <b>Total Registered Users:</b> {user_count}\n"
        f"‣ <b>Active Groups:</b> {len(group_ids)}",
        parse_mode='HTML'
    )


async def send_users_document(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in SUDO_USERS:
        await update.message.reply_text("Only for Sudo users...")
        return

    cursor = user_collection.find({})
    users = [doc async for doc in cursor]

    user_list = "\n".join(user['first_name'] for user in users)

    with open("users.txt", "w") as f:
        f.write(user_list)
    with open("users.txt", "rb") as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f)
    os.remove("users.txt")


async def send_groups_document(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in SUDO_USERS:
        await update.message.reply_text("Only for Sudo users...")
        return

    cursor = top_global_groups_collection.find({})
    groups = [doc async for doc in cursor]

    group_list = "\n\n".join(group['group_name'] for group in groups)

    with open("groups.txt", "w") as f:
        f.write(group_list)
    with open("groups.txt", "rb") as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f)
    os.remove("groups.txt")


# Command handler registration
application.add_handler(CommandHandler('ctop', ctop, block=False))
application.add_handler(CommandHandler('stats', stats, block=False))
application.add_handler(CommandHandler('TopGroups', global_leaderboard, block=False))
application.add_handler(CommandHandler('list', send_users_document, block=False))
application.add_handler(CommandHandler('groups', send_groups_document, block=False))
application.add_handler(CommandHandler('top', leaderboard, block=False))
