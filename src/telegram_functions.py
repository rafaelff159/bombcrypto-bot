from telegram import Bot
import yaml

# Load config file.
stream = open("config.yaml", 'r')
config = yaml.safe_load(stream)

bot_enabled = config['telegram']['enabled']
bot_token = config['telegram']['token_api']
bot_chatID = config['telegram']['chat_id']

if bot_enabled:
    bot = Bot(bot_token)

def telegram_bot_sendtext(bot_message):
    if bot_enabled and type(bot_message) == str:
        return bot.send_message(chat_id = bot_chatID, text = bot_message)

def telegram_bot_sendimage(imagePath):
    if bot_enabled:
        return bot.send_photo(chat_id = bot_chatID, photo = open(imagePath, 'rb'))