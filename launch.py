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


async def start_bot():
    await bot.start(token, bot=True, reconnect=True)


if __name__ == "__main__":
    setts = load_settings()
    token = setts["token"]
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start_bot())
    except KeyboardInterrupt:
        loop.run_until_complete(bot.logout())
        print("I'm going to sleep, master!")
        # todo: cancel tasks
    except Exception as e:
        print(f"[ERROR] {e}")
    else:
        print("I'm going to sleep, master!")
    finally:
        loop.close()
