from decouple import config
import os
os.environ["TOTALITY_ENDPOINT"]=config("TOTALITY_ENDPOINT")

from web3 import Web3, HTTPProvider
import inspect

BOT_TOKEN=config("BOT_TOKEN")
TOTALITY=config("TOTALITY_ENDPOINT")
CHAIN_ID=3
WEB3_ENDPOINT=Web3(HTTPProvider(config('WEB3_ENDPOINT')))
