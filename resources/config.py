import os
from dotenv import load_dotenv

load_dotenv()

BOT_NAME = "Sinful Bot"
BOT_TOKEN = os.getenv("BOT_TOKEN")

SINFUL_SERVER_ID = os.getenv("SINFUL_SERVER")
MY_SERVER_ID = os.getenv("MY_SERVER")
