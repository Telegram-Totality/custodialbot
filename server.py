from flask import Flask
from flask import request, jsonify
import requests.exceptions
import totality
import settings
import database
import telegram
app = Flask(__name__)

@app.route('/limit/<userid>', methods=["GET"])
def limit(userid):
    secret = request.headers.get("Authorization")
    try:
        bot_info = totality.get_bot_info(secret)
    except requests.exceptions.HTTPError:
        return jsonify({
            "success": False,
            "message": "Unknown secret",
            "code": "UNKNOWN_SECRET"}), 400

    with database.session_scope() as s:
        return jsonify({"limit": database.SpendingLimits.getsert(s, userid, secret, bot_info["erc20"]).get_user_limit()})


@app.route('/tx/<txhash>', methods=["POST"])
def execute_tx(txhash):
    secret = request.headers.get("Authorization")
    user = request.headers.get("userid")
    try:
        bot_info = totality.get_bot_info(secret)
    except requests.exceptions.HTTPError:
        return jsonify({
            "success": False,
            "message": "Unknown secret",
            "code": "UNKNOWN_SECRET"}), 400

    call = totality.get_call_data(txhash)
    if call["network"] != settings.WEB3_CHAIN_ID:
        return jsonify({
            "success": False,
            "message": "Wrong network id",
            "code": "WRONG_NETWORK"}), 400

    if call["function"] != "transfer":
        return jsonify({
            "success": False,
            "message": "Function is not transfer function",
            "code": "WRONG_FUNCTION"}), 400

    if call["address"] != settings.TOKENS.get(bot_info["erc20"]): #todo, get from tty-com
         return jsonify({
            "success": False,
            "message": "Contract is not righ contract, got %s" % settings.TOKENS.get(bot_info["erc20"]),
            "code": "WRONG_CONTRACT"}), 400

    user_limit = None
    with database.session_scope() as s:
        limit = database.SpendingLimits.getsert(s, user, secret, bot_info["erc20"])
        if not totality.create_result(txhash):
            return jsonify({
                "success": False,
                "message": "Failed to create transaction, probably already pending",
                "code": "FAIL_EXEC"}), 400

        if call["params"]["amount"] == 0 or not limit.claim(call["params"]["amount"]):
            return jsonify({
            "success": False,
            "message": "Amount is zero, or exceeding spending limit",
            "code": "WRONG_AMOUNT"}), 400

        user_limit = limit.get_user_limit()

    def call_user_limit():
        if bot_info["erc20"] == "USDC":
            return call["params"]["amount"] / 1000000
        return call["params"]["amount"] / 1000000000000000000

    acc = totality.AccountT.from_storage(user)
    tx = acc.do_tx(call)
    if tx:
        l = {"success": True, "message": "success", "tx": tx}
    else:
        l = {"success": False, "message": "Something went wrong", "code": "UNKNOWN_ERROR"}
    totality.update_result(txhash, l)

    bot = telegram.Bot(token=settings.BOT_TOKEN)
    bot.sendMessage(chat_id=user, text="%s transferred %s %s to %s, %s %s approval left." % (
        bot_info["handle"], call_user_limit(), bot_info["erc20"], call["params"]["recipient"], user_limit, bot_info["erc20"]))

    return jsonify(l)