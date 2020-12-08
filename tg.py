import settings
import threading
import time
import requests.exceptions

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

import database
import ethereum
from totality import AccountT, post_address, get_call_data, create_result, update_result, get_bot_info

PK, LIMIT = range(2)
# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    user_data = context.user_data

    def check_for_account():
        acc = AccountT.from_storage(update.effective_user.id)
        if not acc or acc.address != update.effective_user.address:
            update.message.reply_text("Hi, please setup your keys first.")
            return False
        return True

    payload = update.message.text[7:]
    if payload.startswith("limit-") and check_for_account():
        secret = payload[6:]
        try:
            bot_info = get_bot_info(secret)
        except requests.exceptions.HTTPError:
            update.message.reply_text("Invalid referal")
            return

        with database.session_scope() as s:
            limit = database.SpendingLimits.getsert(s, update.effective_user.address, secret, bot_info["erc20"])

            update.message.reply_text("%s is asking you to change your spending limit, your current limit"
            " is %s %s, change to?" % (bot_info["handle"], limit.get_user_limit(), limit.token),
            reply_markup=ReplyKeyboardMarkup([["10", "100", "1000"]], one_time_keyboard=True))
        user_data["secret"] = secret
        return LIMIT

    if "call_hash" in user_data:
        del user_data['call_hash']


    update.message.reply_text("""This is a bot that enables your to communicate with the Telegram Totality network.

This is a custodial way to communicate with the bots, which means your private keys will be stored on my server.

If you prefer a non custodial way, controlling your own private key. Please download one of the open source Totality apps.
""", reply_markup=ReplyKeyboardRemove())

    if not update.effective_user.address:
        update.message.reply_text("Please share your existing private key, or create a /new account. (/help)")
        return PK

    acc = AccountT.from_storage(update.effective_user.id)
    if not acc or acc.address != update.effective_user.address:
        update.message.reply_text("You have been using Totality products earlier, haven't you? "
            "The address is <b>%s</b>. Please share the private key of this address. (/help)" % update.effective_user.address,
            parse_mode="HTML")
        return PK

    update.message.reply_text("Your address <b>%s</b> is setup." % update.effective_user.address, parse_mode="HTML")
    return ConversationHandler.END


def pk(update, context):
    pk = update.message.text
    acc = AccountT.from_key(pk)
    if update.effective_user.address:
        if acc.address != update.effective_user.address:
            update.message.reply_text("Private does not match you address")
            return
        else:
            update.message.reply_text("Private key set")
    else:
        post_address(update.effective_user, acc.address)
        update.message.reply_text("Your address is %s" % acc.address)

    acc.store_key(update.effective_user.id)
    return ConversationHandler.END

def pk_new(update, context):
    if update.effective_user.address:
        update.message.reply_text("Looks like you already have an account, press /start")
        return ConversationHandler.END

    acc = AccountT.create()
    acc.store_key(update.effective_user.id)
    post_address(update.effective_user, acc.address)
    update.message.reply_text("Your address is %s" % acc.address)
    return ConversationHandler.END

def pk_help(update, context):
    update.message.reply_text("Please share the hex format with a length of 64, exluding 0x prefix.")

def cancel(update, context):
    update.message.reply_text('Bye! I hope we can talk again some day.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def limit(update, context):
    secret = context.user_data["secret"]
    del context.user_data['secret']

    with database.session_scope() as s:
        limit = database.SpendingLimits.getsert(s, update.effective_user.id, secret, None)
        limit.new_limit(int(update.message.text))
        update.message.reply_text("Your new limit is %s" % limit.get_user_limit()),

    return ConversationHandler.END

def balances(update, context):
    rt = ""
    for ticker, address in settings.TOKENS.items():
        amount = ethereum.balance_of(address, update.effective_user.address)
        rt += "%s - %s\n" % (ticker, amount)

    update.message.reply_text("Your balances are: \n\n%s" % rt)

def pk_print(update, context):
    user = AccountT.from_storage(update.effective_user.id)
    update.message.reply_text("Your private key is: %s" % user.key_str)

def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(settings.BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            PK: [MessageHandler(Filters.regex('^[0-9a-fA-F]{64,64}$'), pk),
                CommandHandler('help', pk_help),
                CommandHandler('new', pk_new)],
            LIMIT: [MessageHandler(Filters.regex('^\d+$'), limit)]

        },

        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('start', start)]
    )
    dp.add_handler(CommandHandler("balances", balances))
    dp.add_handler(CommandHandler("pk", pk_print))
    dp.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    t = threading.current_thread()
    while True:
        if not getattr(t, "do_run", True):
            updater.stop()
            break
        time.sleep(1)