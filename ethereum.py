import settings
from web3 import Web3, HTTPProvider

abi = [{
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [
            {
                "name": "",
                "type": "uint8"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },{
        "constant": True,
        "inputs": [
            {
                "name": "_owner",
                "type": "address"
            }
        ],
        "name": "balanceOf",
        "outputs": [
            {
                "name": "balance",
                "type": "uint256"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }]

def balance_of(contract, user, print_user=True):
    WEB3_ENDPOINT= Web3(HTTPProvider(settings.WEB3_ENDPOINT))
    erc20 = WEB3_ENDPOINT.eth.contract(address=contract, abi=abi)

    divider = 1
    if print_user:
        decimals = erc20.functions.decimals().call()
        divider = int("1" + decimals * "0")

    return erc20.functions.balanceOf(user).call() / divider

def transfer_some_matic(receipent):
    WEB3_ENDPOINT= Web3(HTTPProvider(settings.WEB3_ENDPOINT))
    return WEB3_ENDPOINT.eth.sendTransaction({
        'to':receipent,
        'gas':500000,
        'gasPrice':2000000000,
        'value': 5000000000000000
    })