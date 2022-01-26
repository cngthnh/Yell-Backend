import json

def genTransactionInfo(transactionDict: dict) -> str:
    return json.dumps(transactionDict)