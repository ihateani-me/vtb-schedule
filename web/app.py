# -*- coding: utf-8 -*-

import asyncio
import sys
from datetime import datetime
from uuid import uuid4

import pytz
from sanic import Blueprint, Sanic
from sanic import __version__ as sanicver
from sanic.exceptions import NotFound
from sanic.log import logger
from sanic.response import html, json
from sanic_motor import BaseModel
from sanic_openapi import doc, swagger_blueprint

import ujson
from routes.hololive import holobp
from routes.nijisanji import nijibp
from routes.others import otherbp
from utils.memcache import MemcachedBridge

RANDOMIZED_UUID_API = str(uuid4())

app = Sanic("vtbili")
app.blueprint(swagger_blueprint)
settings = dict(
    MOTOR_URI="mongodb://127.0.0.1:12345/DATABASE_NAME",  # Modify this.
    MEMCACHED_HOST="127.0.0.1",  # comment out this if you don't want to use it.
    MEMCACHED_PORT=11211,  # comment out this if you don't want to use it.
    API_MASTER_KEY="SUPERSECRET_APIMASTERKEY",  # Modify this.
    API_SECRET_KEY=RANDOMIZED_UUID_API,
    APP_API_KEY_UPDATE=[],
    APP_EXCLUDE_IPS_LIMIT=[],
    APP_IMPLEMENT_RATE_LIMIT=False,
    # Don't modify anything below here
    API_VERSION="0.4.0",
    API_TITLE="VTubers BiliBili Schedule API",
    API_CONTACT_EMAIL="noaione0809@gmail.com",
    API_LICENSE_NAME="MIT License",
    API_LICENSE_URL="https://github.com/noaione/vthell/blob/master/LICENSE",
)

API_DESC = """A VTubers **API endpoint** for
the new [BiliBili scheduling system](https://live.bilibili.com/p/html/live-web-calendar).

This API are updating automatically using cronjob:
\- **Every 1 minute** for YouTube Live Streams data.
\- **Every 2 minutes** for YouTube Upcoming Streams data.
\- **Every 2 minutes** for BiliBili Live Streams data.
\- **Every 4 minutes** for BiliBili Upcoming Streams data.
\- **Every 6 hours** for Channels Info/Stats.<br><br>"""  # noqa: W605,E501
API_DESC_LIMIT = """This API also implement a Rate Limiting:
\- **3 requests** per **minute**
\- **1500 requests** per **day**<br><br>"""  # noqa: W605,E501
API_DESC_END = """You could contact me at **Discord**: _N4O#8868_
If you need more Other VTubers to add to the list."""

app.config.update(settings)
if app.config.get("APP_IMPLEMENT_RATE_LIMIT", True):
    API_DESC += API_DESC_LIMIT
API_DESC += API_DESC_END

app.config["API_DESCRIPTION"] = API_DESC
app.config.FORWARDED_SECRET = (
    "e51bfddc277b46a194f81c146b3b4606"  # Used for reverse proxy
)

adminbp = Blueprint("Admin", "/admin", strict_slashes=True)

BaseModel.init_app(app)

DEFAULT_HOMEPAGE = """<code>Welcome to ihateani.me simple BiliBili VTuber Scheduler API Endpoint
<br>
Created by N4O<br>
Contact me at Discord: N4O#8868<br>
<br>
Current time: <span id="current_dt"></span><br>
Detailed API Documentation<br>
--> <a href="/swagger">API Docs</a> (Swagger UI)<br>
<br>
Supported currently are:<br>
- HoloLive<br>
- Nijisanji<br>
- Other VTuber<br>
<br>
Endpoint:<br>
- <a href="/live">`/live`</a> for Hololivers Live/Upcoming Bili streams<br>
- <a href="/channels">`/channels`</a> for Hololivers BiliBili channels stats<br>
- <a href="/nijisanji/live">`/nijisanji/live`</a> for Nijisanji Live/Upcoming Bili streams<br>
- <a href="/nijisanji/channels">`/nijisanji/channels`</a> for Nijisanji BiliBili channels stats<br>
- <a href="/other/upcoming">`/other/upcoming`</a> for Other VTuber<br>
- <a href="/other/channels">`/other/channels`</a> to check supported "Other VTuber"<br>
- <a href="/other/yt/live">`/other/yt/live`</a> to see upcoming/live for some other vtuber.<br>
- <a href="/other/yt/channels">`/other/yt/channels`</a> to see supported channels for youtube version of other vtuber.<br>
<br>
Dataset Used:<br>
- vtbs.moe<br>
<br>
Refresh/Cache Rate:<br>
- Channels: Every 6 hours<br>
- Upcoming (Bili): Every 4 minutes<br>
- Live (Bili): Every 2 minutes<br>
- Upcoming (YT): Every 2 minutes<br>
- Live (YT): Every 1 minute<br>
<br>
Rate Limiting [If activated]:<br>
- Per Minute: 3 requests max (Without API Key.)<br>
- Per days: 1500 requests max (Without API Key.)<br>
<br>
Backend:<br>
"""
EXTENSION_HOMEPAGE = """- Framework: Sanic v{sv} (Python {pyv})<br>
- Database: MongoDB Community v4.2.3</code>
"""
SCRIPTS_HOMEPAGE = r"""<script>
    const clock = document.getElementById("current_dt");
    clock.textContent = (new Date()).toString();
    setInterval(function(){
        clock.textContent = (new Date()).toString();
        },
        1000
    );
</script>
"""


@app.exception(NotFound)
async def handle_404(request, exception):
    logger.warn(f"URL {request.path} not found, sending current UTC Time...")
    current_time = int(
        round(datetime.now(tz=pytz.timezone("UTC")).timestamp())
    )
    return json({"time": current_time}, status=404)


@app.listener("before_server_start")
async def start_memcached(app: Sanic, loop):
    logger.info("[memcached] Trying to connect to memcached database.")
    try:
        mem_host, mem_port = (
            app.config.get("MEMCACHED_HOST"),
            app.config.get("MEMCACHED_PORT", 11211),
        )
        if not mem_host:
            logger.warn("[memcached] No host provided, skipping...")
            app.mdb = None
            return True
        logger.debug(f"[memcached] Host: {mem_host} | Port: {mem_port}")
        app.mdb: MemcachedBridge = MemcachedBridge(
            host="127.0.0.1", port=11211, loop=loop
        )
        logger.info("[memcached] Connected!")
        logger.info("[memcached] Caching from remote database.")
        any_ips = await app.mdb.get("ip_addrs")
        if not any_ips:
            logger.info("There's no IP registered, creating one...")
            await app.mdb.set("ip_addrs", [])
        logger.info("[memcached] Cached to local memcache.")
    except Exception as e:
        logger.error(e)
        logger.info("[memcached] Failed to connect.")
        logger.info(
            "[memcached] Please use this key for API Auth: {}".format(
                app.config["API_SECRET_KEY"]
            )
        )
        app.mdb = None
    return True


@app.listener("before_server_stop")
async def stop_memcached(app, loop):
    if isinstance(app.mdb, MemcachedBridge):
        logger.info("[memcached] Closing connection...")
        await app.mdb.close()
        logger.info("[memcached] Connection closed.")


async def fetch_token_from_cache() -> list:
    if isinstance(app.mdb, MemcachedBridge):
        tken_set = await app.mdb.get("token_key_list")
        if not tken_set:
            return []
        return tken_set
    return []


@app.middleware("response")
async def before_response(request, response):
    response.headers["server-backend"] = "Sanic-{}".format(sanicver)
    response.headers["server-api-version"] = app.config.get(
        "API_VERSION", "UNKNOWN"
    )
    response.headers["x-xss-protection"] = "1; mode=block"
    if app.config.get("APP_IMPLEMENT_RATE_LIMIT", True):
        ip_addr = request.remote_addr
        r_path = request.path.rstrip("/")
        ip_rate_data = {}
        if isinstance(app.mdb, MemcachedBridge):
            ip_rate_data = await app.mdb.get(ip_addr)
        if isinstance(ip_rate_data, dict):
            if ip_rate_data:
                response.headers["X-Rate-Limit"] = ip_rate_data[r_path][
                    "limit"
                ]
                response.headers["X-Rate-Limit-Day"] = ip_rate_data[r_path][
                    "limit_day"
                ]


@app.middleware("request")
async def check_rate_limiting(request):
    if not app.config.get("APP_IMPLEMENT_RATE_LIMIT", True):
        return
    exempted_path = ["/", "/favicon.ico", "/admin/token", "/admin/limit"]
    exempted_path_startswith = ["/swagger"]
    r_path = request.path.rstrip("/")
    if r_path in exempted_path:
        return
    for exempt_st in exempted_path_startswith:
        if r_path.startswith(exempt_st):
            return
    if not isinstance(app.mdb, MemcachedBridge):
        return
    access_log = f"Remote IP {request.remote_addr} connected to {r_path}"
    logger.info(access_log)
    ip_addr = request.ip
    if ip_addr == "127.0.0.1":
        ip_addr = request.remote_addr
    if ip_addr in ("127.0.0.1", "::1", "10.0.0.1", "localhost"):
        return
    available_token: list = await fetch_token_from_cache()
    available_token.append(app.config["API_MASTER_KEY"])
    excluded_ips = app.config.get("APP_EXCLUDE_IPS_LIMIT", [])
    if ip_addr in excluded_ips:
        return
    token = request.headers.get("X-API-Key", "")
    if not token:
        token = request.token
    if token:
        if token in available_token:
            return
    ip_addr_data = await app.mdb.get("ip_addrs")
    ip_rate_data = await app.mdb.get(ip_addr)
    if not ip_rate_data:
        ip_rate_data = {r_path: {"limit": 3, "limit_day": 1500}}
    if r_path not in ip_rate_data:
        ip_rate_data[r_path] = {"limit": 3, "limit_day": 1500}
    if ip_addr not in ip_addr_data:
        ip_addr_data.append(ip_addr)
    await app.mdb.set("ip_addrs", ip_addr_data)
    if ip_rate_data[r_path]["limit_day"] <= 0:
        return json(
            {
                "error": "you already reach 1500 requests per day, please try again tommorow"
            },
            429,
            {
                "X-Rate-Limit": ip_rate_data["limit"],
                "X-Rate-Limit-Day": ip_rate_data["limit_day"],
            },
        )
    if ip_rate_data[r_path]["limit"] <= 0:
        return json(
            {
                "error": "you already reach 3 requests per minute, please try again in the next minute"
            },
            429,
            {
                "X-Rate-Limit": ip_rate_data["limit"],
                "X-Rate-Limit-Day": ip_rate_data["limit_day"],
            },
        )
    ip_rate_data[r_path]["limit"] -= 1
    ip_rate_data[r_path]["limit_day"] -= 1
    await app.mdb.set(ip_addr, ip_rate_data)


def validate_data(data, type_data):
    if not data:
        return False
    if not isinstance(data, type_data):
        return False
    return True


async def fetch_key_from_jsforms(request, key):
    json_data = request.json
    forms_data = request.form
    if not json_data and not forms_data:
        return None
    val = None
    if json_data and not val:
        val = json_data.get(key, None)
    if forms_data and not val:
        val = forms_data.get(key, None)
    return val


@adminbp.get("/token")
@doc.summary("List available API token.")
@doc.description("A list of registered token in the database.")
@doc.consumes(
    doc.String(name="X-API-Key", description="Master API Key to see API Key"),
    location="header",
    required=True,
    content_type="application/json",
)
@doc.produces(
    {"token": doc.List([doc.String("A token")])},
    description="Token list results.",
    content_type="application/json",
)
async def list_token_api(request):
    token = request.headers.get("X-API-Key", None)
    if not token:
        token = request.token
    if token != app.config["API_MASTER_KEY"]:
        return json({"error": "not a valid master API key."}, 403)
    if not isinstance(app.mdb, MemcachedBridge):
        return json(
            {
                "error": "sorry, the server haven't setup the proper requirements for generating new token."
            },
            500,
        )
    token_set = await fetch_token_from_cache()
    return json({"token": token_set})


@adminbp.post("/token")
@doc.summary("Generate new token for auth.")
@doc.description(
    "Generate a new API token/key for use.\nPlease contact N4O#8868 at Discord if you want a key."
)
@doc.consumes(
    doc.String(
        name="X-API-Key", description="Master API Key to generate new API Key"
    ),
    location="header",
    required=True,
    content_type="application/json",
)
@doc.produces(
    {"token": doc.String("Generated token string ready to use.")},
    description="Generated token results.",
    content_type="application/json",
)
async def add_new_token_api(request):
    token = request.headers.get("X-API-Key", None)
    # token_set = [app.config["API_SECRET_KEY"], app.config["API_MASTER_KEY"]]
    if not token:
        token = request.token
    if token != app.config["API_MASTER_KEY"]:
        return json({"error": "not a valid master API key."}, 403)
    if not isinstance(app.mdb, MemcachedBridge):
        return json(
            {
                "error": "sorry, the server haven't setup the proper requirements for generating new token."
            },
            500,
        )
    db_token = await fetch_token_from_cache()
    gen_token = str(uuid4())
    if gen_token not in db_token:
        old_data = app.config.get("APP_API_KEY_UPDATE", [])
        old_data.append({"token": gen_token, "method": "add"})
        app.config["APP_API_KEY_UPDATE"] = old_data
        db_token.append(gen_token)
    await app.mdb.set("token_key_list", db_token)
    return json({"token": gen_token})


@adminbp.delete("/token")
@doc.summary("Delete token from DB.")
@doc.description("Delete API token/key from internal memory DB.")
@doc.consumes(
    doc.String(
        name="X-API-Key", description="Master API Key to remove API Key"
    ),
    location="header",
    required=True,
    content_type="application/json",
)
@doc.consumes(
    doc.JsonBody({"t": doc.String("Token to delete.", True)}),
    content_type="application/json",
    location="body",
    required=True,
)
async def delete_api_key(request):
    token = request.headers.get("X-API-Key", None)
    if not token:
        token = request.token
    if token != app.config["API_MASTER_KEY"]:
        return json({"error": "not a valid master API key."}, 403)
    if not isinstance(app.mdb, MemcachedBridge):
        return json(
            {
                "error": "sorry, the server haven't setup the proper requirements for generating new token."
            },
            500,
        )
    token2del = await fetch_key_from_jsforms(request, "t")
    if not validate_data(token2del, str):
        return json(
            {
                "error": "please provide `t` in json/forms body and set it as a string."
            },
            400,
        )
    token_set = await fetch_token_from_cache()
    if token2del in token_set:
        old_data = app.config.get("APP_API_KEY_UPDATE", [])
        old_data.append({"token": token2del, "method": "delete"})
        app.config["APP_API_KEY_UPDATE"] = old_data
        token_set.remove(token2del)
    await app.mdb.set("token_key_list", token_set)
    return json({"message": "token successfully deleted."})


app.blueprint(holobp)
app.blueprint(nijibp)
app.blueprint(otherbp)
app.blueprint(adminbp)


async def flush_rate_min():
    while True:
        logger.info("[RL-Min] Flushing all IPs.")
        if isinstance(app.mdb, MemcachedBridge):
            ip_addrs = await app.mdb.get("ip_addrs")
            for ip_addr in ip_addrs:
                logger.info(f"[RL-Min] Flushing: {ip_addr}")
                cur_data = await app.mdb.get(ip_addr)
                for path in cur_data.keys():
                    cur_data[path]["limit"] = 3
                await app.mdb.set(ip_addr, cur_data)
        logger.info("[RL-Min] Sleeping...")
        await asyncio.sleep(60)


async def flush_rate_day():
    while True:
        logger.info("[RL-Day] Flushing all IPs.")
        if isinstance(app.mdb, MemcachedBridge):
            ip_addrs = await app.mdb.get(b"ip_addrs")
            ip_addrs = ujson.loads(ip_addrs.decode("utf-8"))
            for ip_addr in ip_addrs:
                logger.info(f"[RL-Day] Flushing: {ip_addr}")
                cur_data = await app.mdb.get(ip_addr)
                for path in cur_data.keys():
                    cur_data[path]["limit_day"] = 1500
                await app.mdb.set(ip_addr, cur_data)
        logger.info("[RL-Day] Sleeping...")
        await asyncio.sleep(86400)


if app.config.get("APP_IMPLEMENT_RATE_LIMIT", True):
    app.add_task(flush_rate_min())
    app.add_task(flush_rate_day())


@app.route("/")
@doc.exclude(True)
async def home(request):
    pyver = "{0.major}.{0.minor}.{0.micro}".format(sys.version_info)
    html_text = (
        DEFAULT_HOMEPAGE
        + EXTENSION_HOMEPAGE.format(sv=sanicver, pyv=pyver)
        + SCRIPTS_HOMEPAGE
    )
    return html(html_text)


if __name__ == "__main__":
    logger.info("Starting server...")
    logger.info(f"Randomized API Key: {app.config['API_SECRET_KEY']}")
    logger.info("You still are able to use the master API Key.")
    app.run(host="127.0.0.1", port=8000, debug=False, access_log=True)
