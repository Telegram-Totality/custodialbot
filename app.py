import settings
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

from totality import AccountT, post_address, get_call_data, create_result, update_result

PK, TX = range(2)
# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    user_data = context.user_data

    def check_for_tx():
        acc = AccountT.from_storage(update.effective_user.id)
        if not acc or acc.address != update.effective_user.address:
            update.message.reply_text("Hi, please setup your keys first.")
            return

        call_hash = payload[8:]
        data = get_call_data(call_hash)
        if data:
            reply_keyboard = [['Yes', 'No']]
            user_data["call_hash"] = call_hash
            update.message.reply_text(
                "Do you want to call the <b>%s</b> function on <a href='ropsten.etherscan.io/address/%s'>this address</a>" % (data["function"], data["address"]),
                parse_mode="HTML", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
            return TX

    payload = update.message.text[7:]
    if payload.startswith("tgtotal-"):
        ctx = check_for_tx()
        if ctx:
            return ctx

    if "call_hash" in user_data:
        del user_data['call_hash']

    update.message.reply_text("""This is a bot that enables your to communicate with the Telegram Totality network.

This is a custodial way to communicate with the bots, which means your private keys will be stored on my server.

If you prefer a non custodial way, controlling your own private key. Please download one of the open source Totality apps.
""")

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

def tx(update, context):
    if update.message.text == "No":
        return ConversationHandler.END

    acc = AccountT.from_storage(update.effective_user.id)
    assert acc.address == update.effective_user.address, "Address is wrong"

    user_data = context.user_data
    call_hash = user_data["call_hash"]

    data = get_call_data(call_hash)

    create_result(call_hash)
    tx = acc.do_tx(data)
    if tx:
        update_result(call_hash, {"success": True, "message": "success", "tx": tx})
    else:
        update_result(call_hash, {"success": False, "message": "Something went wrong", "tx": None})

    del user_data["call_hash"]
    update.message.reply_text("Succesfully published transaction")


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
            TX: [MessageHandler(Filters.regex('^(Yes|No)$'), tx)]

        },

        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('start', start)]
    )

    dp.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()