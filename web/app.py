# -*- coding: utf-8 -*-

import sys
from datetime import datetime
from uuid import uuid4

import pytz
from sanic import Sanic
from sanic import __version__ as sanicver
from sanic.exceptions import NotFound
from sanic.log import logger
from sanic.response import html, json
from sanic_motor import BaseModel
from sanic_openapi import doc, swagger_blueprint

from routes.hololive import holobp
from routes.nijisanji import nijibp
from routes.others import otherbp
from routes.others_youtube import otherytbp

RANDOMIZED_UUID_API = str(uuid4())

app = Sanic("vtbili")
app.blueprint(swagger_blueprint)
settings = dict(
    MOTOR_URI="mongodb://127.0.0.1:12345/DATABASE_NAME",  # Modify this.
    # Don't modify anything below here
    API_VERSION="0.5.0",
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


@app.middleware("response")
async def before_response(request, response):
    response.headers["server-backend"] = "Sanic-{}".format(sanicver)
    response.headers["server-api-version"] = app.config.get(
        "API_VERSION", "UNKNOWN"
    )
    response.headers["x-xss-protection"] = "1; mode=block"


app.blueprint(holobp)
app.blueprint(nijibp)
app.blueprint(otherbp)
app.blueprint(otherytbp)


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
    app.run(host="127.0.0.1", port=8000, debug=False, access_log=True)
