import settings
import requests
import os
import json

from web3 import Web3, HTTPProvider
from eth_account import Account
from eth_account.signers.local import LocalAccount
from eth_utils.curried import combomethod

from cachetools import cached, TTLCache
from web3 import Web3

storage = os.path.join("storage")

def post_address(user, address):
    user.address_clear()
    r = requests.post("%s/tg/%s" % (settings.TOTALITY, str(user.id)),
        data={"address": address}
    )
    r.raise_for_status()

def create_result(call_hash):
    r = requests.post("%s/result/%s" % (settings.TOTALITY, call_hash))
    return r.status_code == 200

def update_result(call_hash, result):
    r = requests.put("%s/result/%s" % (settings.TOTALITY, call_hash),
        json=result)
    r.raise_for_status()

@cached(TTLCache(maxsize=256, ttl=600))
def get_call_data(call_hash):
    r = requests.get("%s/call/%s" % (settings.TOTALITY, call_hash),
    )
    if r.status_code != 200:
        return None
    return r.json()

class LocalAccountT(LocalAccount):
    @property
    def key_str(self):
        return self.key.hex()

    def store_key(self, id):
        with open(os.path.join(storage, str(id)), "w") as f:
            f.write(self.key_str)

    def do_tx(self, data):
        WEB3_ENDPOINT = None
        if data["network"] == 1:
            WEB3_ENDPOINT=Web3(HTTPProvider("https://mainnet.infura.io/v3/%s" % settings.INFURA_TOKEN))
        elif data["network"] == 3:
            WEB3_ENDPOINT=Web3(HTTPProvider("https://ropsten.infura.io/v3/%s" % settings.INFURA_TOKEN))
        else:
            return None

        address = Web3.toChecksumAddress(data["address"])
        abi = [data["abi"],]
        contract = WEB3_ENDPOINT.eth.contract(address=address, abi=abi)

        func = contract.get_function_by_name(data["function"])
        # json list order is preserverd (fingers crossed)
        x = func(*data["params"].values())
        data = {
            'chainId': data["network"],
            'gas': data["gasLimit"],
            'gasPrice': data["gasPrice"],
            'nonce': WEB3_ENDPOINT.eth.getTransactionCount(self.address),
            'value': data["weiValue"]
        }
        ctr = x.buildTransaction(data)
        signed_tx = WEB3_ENDPOINT.eth.account.sign_transaction(ctr, self.privateKey)
        WEB3_ENDPOINT.eth.sendRawTransaction(signed_tx.rawTransaction)
        return Web3.toHex(signed_tx["hash"])

class AccountT(Account):
    @combomethod
    def from_key(self, private_key):
        key = self._parsePrivateKey(private_key)
        return LocalAccountT(key, self)

    @combomethod
    def from_storage(self, id):
        f = os.path.join(storage, str(id))
        if not os.path.exists(f):
            return None

        with open(f, "r") as f:
            return self.from_key(f.read().strip())



