from decouple import config
import os
os.environ["TOTALITY_ENDPOINT"]=config("TOTALITY_ENDPOINT")

import inspect

BOT_TOKEN=config("BOT_TOKEN")
TOTALITY=config("TOTALITY_ENDPOINT")
WEB3_ENDPOINT=config('WEB3_ENDPOINT')
WEB3_CHAIN_ID=config('WEB3_CHAIN_ID',  cast=int)

TOKENS = {
    "DAI": None,
    "USDC": None
}
if WEB3_CHAIN_ID == 80001:
    TOKENS["DAI"] = "0x2Aae2f090085265cd77d90b82bb8B7a908738815"
    TOKENS["USDC"] = "0x2Aae2f090085265cd77d90b82bb8B7a908738815"
elif WEB3_CHAIN_ID == 137:
    TOKENS["DAI"] = "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063"
    TOKENS["USDC"] = "0x5FaB5764f263c5CE93424F8c45e46A742Cc5C8d6"

FLASK_HOST=config("FLASK_HOST", default="localhost")
FLASK_PORT=config("FLASK_PORT", cast=int, default=5001)
