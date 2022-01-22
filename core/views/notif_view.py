from ..models.models import Notification
from typing import List
import json

def parseNotifications(notifications: List[Notification]):
    result = []
    for notif in notifications:
        result.append(notif.dict())
    return json.dumps(result)