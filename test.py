import re, json, config, datetime
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


# ref = db.reference()
# ref.update({"settings": {"volume": 20}})

# data = db.reference("settings")
# data.update({"volume": 40})

timeString = "2022-05-06 17:34:17.389733+00:00"
myDT = datetime.datetime.fromisoformat(timeString)

print(myDT.astimezone())
