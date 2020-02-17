import asyncio
from mainbot import bot
from utils.checks import check_create_folder, check_copy_file
import json
import aiomysql
from utils.funx import Funx


def load_settings():
    check_create_folder("data")
    check_copy_file("data/settings.json")
    with open("data/settings.json") as f:
        print("[INFO] Loaded settings.")
        return json.load(f)


async def start_bot():
    setts = load_settings()
    token = setts["token"]
    db_ip = setts["db_ip"]
    db_user = setts["db_user"]
    db_pass = setts["db_pass"]
    db_name = setts["db_name"]
    bot.owner_ids = set(setts["owner_ids"])
    bot.consts = setts["constants"]
    bot.prefixes = setts["prefixes"]
    bot.pool = await aiomysql.create_pool(host=db_ip, port=3306, user=db_user, password=db_pass, db=db_name, minsize=10, maxsize=60)
    bot.funx = Funx(bot)
    await bot.start(token, bot=True, reconnect=True)


if __name__ == "__main__":
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
