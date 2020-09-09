from decouple import config
import os
os.environ["TOTALITY_ENDPOINT"]=config("TOTALITY_ENDPOINT")

import inspect

BOT_TOKEN=config("BOT_TOKEN")
TOTALITY=config("TOTALITY_ENDPOINT")
INFURA_TOKEN=config('INFURA_TOKEN')

