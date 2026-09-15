import os, json
from dotenv import load_dotenv

load_dotenv()

BOT_NAME = "Sinful Bot"
BOT_TOKEN = os.getenv("BOT_TOKEN")

SINFUL_SERVER_ID = os.getenv("SINFUL_SERVER")
SINFUL_GENERAL_ID = os.getenv("SINFUL_GENERAL")
SINFUL_TEST_ID = os.getenv("SINFUL_TEST")
MY_SERVER_ID = os.getenv("MY_SERVER")
MY_GENERAL_ID = os.getenv("MY_GENERAL")


SPOTIFY_CLIENT_ID = os.getenv("CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("CLIENT_SECRET")

BOT_ACK = os.getenv("BOT_ACK")

with open("sinful-server-bot-firebase.json") as fb:
    FIREBASE_CONFIG = json.load(fb)
