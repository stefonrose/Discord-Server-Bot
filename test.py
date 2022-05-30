import re, json, config, datetime
from typing import List
import firebase_admin
from firebase_admin import credentials, db

firebase_cred = credentials.Certificate(config.FIREBASE_CONFIG)
databaseApp = firebase_admin.initialize_app(
    firebase_cred,
    {"databaseURL": "https://sinful-server-bot-default-rtdb.firebaseio.com/"},
)


def isURL(query):
    regex = (
        "((http|https)://)(www.)?"
        + "[a-zA-Z0-9@:%._\\+~#?&//=]"
        + "{2,256}\\.[a-z]"
        + "{2,6}\\b([-a-zA-Z0-9@:%"
        + "._\\+~#?&//=]*)"
    )

    p = re.compile(regex)

    if re.search(p, query):
        return True
    else:
        return False


# data = {
#     "969860560927744030": {
#         "properties": {"volume": 20, "playing_message_id": 0, "queue_message_id": 0}
#     },
#     "505506594218442753": {
#         "properties": {"volume": 20, "playing_message_id": 0, "queue_message_id": 0}
#     },
# }

# ref = db.reference()
# ref.update(data)

# data = db.reference("settings")
# data.update({"volume": 40})

timeString = "2022-05-06 17:34:17.389733+00:00"
myDT = datetime.datetime.fromisoformat(timeString)

print(myDT.astimezone())

list = [1, 2, 3]


def popFrom(l: List[int]):
    for n in range(1, 0):
        l.pop()
    print(l)
    print(list)


popFrom(list)
