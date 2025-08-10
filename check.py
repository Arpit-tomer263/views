# from telegram import Update
# from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# # Channel IDs
# CHANNEL_1_ID = -1002719518474  # Replace with your source channel ID (bot must be admin here)
# CHANNEL_2_ID = -1002746174961  # Replace with your destination channel ID

# BOT_TOKEN = '7132164278:AAFxch5Tg7ilkG1TehifgA_x227TTuvvJ28'  # Replace with your bot token

# async def forward_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
# 	# Only handle channel posts from the source channel
# 	print(f"Received update: {update}")
# 	if update.channel_post and update.channel_post.chat.id == CHANNEL_1_ID:
# 		try:
# 			await context.bot.forward_message(
# 				chat_id=CHANNEL_2_ID,
# 				from_chat_id=CHANNEL_1_ID,
# 				message_id=update.channel_post.message_id
# 			)
# 		except Exception as e:
# 			print(f"Error forwarding message: {e}")

# def main():
# 	app = ApplicationBuilder().token(BOT_TOKEN).build()
# 	# Listen to channel posts, not just messages
# 	app.add_handler(MessageHandler(filters.ALL & filters.UpdateType.CHANNEL_POST, forward_post))
# 	print("Bot started. Press Ctrl+C to stop.")
# 	app.run_polling()

# if __name__ == '__main__':
# 	main()

a = map(lambda x: x**2, [1, 2, 3, 4])
print(list(a))