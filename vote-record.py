#!/usr/bin/env python

from wsgiref.simple_server import make_server
import json
import datetime
import asyncio
import asyncpg

# Database Connection
with open('data/settings.json', 'r') as fp:
    db_cred = json.load(fp)
db_ip = db_cred["db_ip"]
db_pass = db_cred["db_pass"]
db_user = db_cred["db_user"]
db_name = db_cred["db_name"]
utc_diff = db_cred["constants"]["utc_diff"]
date_format = db_cred["constants"]["date_format"]
dbl_pass = db_cred["constants"]["dbl_pass"]
###############

loop = asyncio.get_event_loop()


async def record_vote(script):
    conn = await asyncpg.connect(host=db_ip, user=db_user, password=db_pass, database=db_name)
    await conn.execute(script)
    await conn.close()


def application(environ, start_response):
    env = environ
    ret = "404 - Page not found"

    if env["PATH_INFO"] == "/vote":
        auth = "HTTP_AUTHORIZATION"
        if auth in env:
            auth = env[auth]
        ret = "503 - Forbidden (Unauthorized)"
        if auth == dbl_pass:
            # the environment variable CONTENT_LENGTH may be empty or missing
            try:
                request_body_size = int(env.get('CONTENT_LENGTH', 0))
            except ValueError:
                request_body_size = 0
                ret = "Error type 1: Missing data object"
            if request_body_size > 0:
                request_body = environ['wsgi.input'].read(request_body_size)
                d = request_body.decode("utf-8")
                try:
                    d = json.loads(d)
                    uid = d["user"]
                    multi = 1
                    if d["isWeekend"]:
                        multi = 2
                    time_utc = datetime.datetime.utcnow()
                    time_now = time_utc + datetime.timedelta(hours=utc_diff)
                    time_now = time_now.strftime(date_format)
                    script = "insert into amathy.votes (user_id, vote_num, last_vote, rewards) values ({0}, {1}, '{2}', {1}) on conflict (user_id) do update set vote_num=votes.vote_num+{1}, last_vote='{2}', rewards=votes.rewards+{1};"
                    script = script.format(uid, multi, time_now)
                    loop.run_until_complete(record_vote(script))
                    ret = "Vote from <{}> recorded successfully! :)".format(uid)
                except Exception as e:
                    print(e)
                    ret = "Error type 2: POST data is not a JSON object"
            # Always escape user input to avoid script injection

    status = '200 OK'
    print(ret)
    response_body = ret
    response_headers = [
        ('Content-Type', 'text/html'),
        ('Content-Length', str(len(response_body)))
    ]

    start_response(status, response_headers)
    return [response_body.encode("utf-8")]


path = ""
port = 85
httpd = make_server(path, port, application)
print("Server running on port {}".format(port))
httpd.serve_forever()
