import asyncio
from mainbot import bot
from utils.checks import FileCheck
import json
import asyncpg
from utils.funx import Funx


def load_settings():
    fchk = FileCheck()
    fchk.check_create_folder("data")
    fchk.check_copy_file("data/settings.json")
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
    db = await asyncpg.create_pool(host=db_ip, user=db_user, password=db_pass, database=db_name)
    bot.pool = db
    bot.funx = Funx(bot)
    await bot.start(token, bot=True, reconnect=True)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start_bot())
    except KeyboardInterrupt:
        loop.run_until_complete(bot.close())
        print("I'm going to sleep, master!")
        # todo: cancel tasks
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        print("I'm going to sleep, master!")
        loop.close()
