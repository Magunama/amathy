import asyncio
from mainbot import bot
from utils.checks import check_create_folder, check_copy_file
import json


def load_settings():
    check_create_folder("data")
    check_copy_file("data/settings.json")
    with open("data/settings.json") as f:
        print("[INFO] Loaded settings.")
        return json.load(f)


async def nasty_startup():
    pass


if __name__ == "__main__":
    setts = load_settings()
    token = setts["token"]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(nasty_startup())
    try:
        bot.run(token, bot=True, reconnect=True)
    except Exception as e:
        print(f"[ERROR] {e}")
    else:
        print("I'm going to sleep, master!")
    finally:
        loop.close()
