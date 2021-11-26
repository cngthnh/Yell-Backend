import json

def genDashboardInfo(dashboardDict: dict) -> str:
    return json.dumps(dashboardDict)