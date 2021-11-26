import json

def genTaskInfo(taskDict: dict) -> str:
    return json.dumps(taskDict)