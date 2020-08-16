from decouple import config
from web3 import Web3, HTTPProvider
import inspect

BOT_TOKEN=config("BOT_TOKEN")
TOTALITY=config("TOTALITY")
CHAIN_ID=3
WEB3_ENDPOINT=Web3(HTTPProvider(config('WEB3_ENDPOINT')))