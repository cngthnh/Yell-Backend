import json

def genUserInfo(userDict: dict) -> str:
    return json.dumps(userDict)