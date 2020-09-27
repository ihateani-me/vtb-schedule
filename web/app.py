# -*- coding: utf-8 -*-

import sys
from datetime import datetime
from uuid import uuid4

import pytz
from pymongo import MongoClient
from sanic import Sanic
from sanic import __version__ as sanicver
from sanic.exceptions import NotFound
from sanic.log import logger
from sanic.response import html, json, redirect, text
from sanic_motor import BaseModel
from sanic_openapi import doc, swagger_blueprint

from routes.changelog import changebp
from routes.hololive import holobp
from routes.nijisanji import nijibp
from routes.others import otherbp
from routes.twitcasting import twitcastbp
from routes.twitch import twitchbp

logger.info("Generating UUID...")
RANDOMIZED_UUID_API = str(uuid4())

app = Sanic("vtbili")
app.blueprint(swagger_blueprint)
settings = dict(
    MOTOR_URI="mongodb://127.0.0.1:12345/DATABASE_NAME",  # Modify this.
    # Don't modify anything below here
    API_VERSION="0.9.0",
    API_SCHEMES=["https"],
    API_MAINTENANCE_MODE=False,
    API_TITLE="VTubers BiliBili Schedule API",
    API_CONTACT_EMAIL="noaione0809@gmail.com",
    API_LICENSE_NAME="MIT License",
    API_LICENSE_URL="https://github.com/noaione/vthell/blob/master/LICENSE",
)

API_DESC = r"""A VTubers **API endpoint** for
the new [BiliBili scheduling system](https://live.bilibili.com/p/html/live-web-calendar).

This API are updating automatically via Python appscheduler:
\- **Every 1 minute** for YouTube/Twitch/Twitcasting Live Streams data.
\- **Every 2 minutes** for YouTube Upcoming Streams data.
\- **Every 2 minutes** for BiliBili Live Streams data.
\- **Every 4 minutes** for BiliBili Upcoming Streams data.
\- **Every 6 hours** for Channels Info/Stats.<br><br>"""  # noqa: W605,E501
API_DESC_END = """You could contact me at **Discord**: _N4O#8868_
If you need more Other VTubers to add to the list."""

app.config.update(settings)
API_DESC += API_DESC_END

app.config["API_DESCRIPTION"] = API_DESC
app.config.FORWARDED_SECRET = "e51bfddc277b46a194f81c146b3b4606"  # Used for reverse proxy

logger.info("Connecting to database...")
BaseModel.init_app(app, name="vtbili", uri=app.config["MOTOR_URI"])

logger.info("Getting database server version...")
sync_dbconn = MongoClient(app.config["MOTOR_URI"])
db_serverinfo = sync_dbconn.server_info()
app.config["MONGODB_DBVERSION"] = db_serverinfo["version"]

HOMEPAGE_HEADERS = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <meta http-equiv=X-UA-Compatible content="IE=edge,chrome=1">
    <title>ihateanime API</title>
    <meta name="description" content="A simple BiliBili Scheduler API Endpoint focused on VTubers">
    <meta name="theme-color" content="#383838">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="manifest" href="/manifest.json">

    <link rel="icon" type="image/png" href="/favicon.png" />
    <link rel="icon" href="/favicon.ico" />

    <style>
        body {
            background-color: #383838;
            color: #dddddd;
            text-shadow: 0 0 2px #fff;
            animation: glow1 1s ease-in-out infinite alternate;
            margin: 0;
            padding: 0;
        }

        .container {
            padding: 0.75rem;
        }

        .nicerbold {
            font-weight: bolder;
            color: white;
            animation: glow2 1.5s ease-in-out infinite alternate;
        }

        a {
            color: #efb973;
            text-decoration: none;
            animation: glowA 1s ease-in-out infinite alternate;
        }
        a:hover {
            text-decoration: underline;
        }
        a:active {
            color: #efb973;
        }

        @keyframes glow1 {
            from {
                text-shadow: 0 0 2px #fff;
            }
            to {
                text-shadow: 0 0 3px #ececec;
            }
        }
        @keyframes glow2 {
            from {
                text-shadow: 0 0 4px #fff;
            }
            to {
                text-shadow: 0 0 5px #ececec;
            }
        }
        @keyframes glowA {
            from {
                text-shadow: 0 0 4px #ab8a60;
            }
            to {
                text-shadow: 0 0 5px #ab8a60;
            }
        }

        .scanlines {
            position: relative;
            overflow: hidden;
            overflow-y: auto;
        }

        .scanlines:before, .scanlines:after {
            display: block;
            pointer-events: none;
            content: '';
            position: absolute;
        }

        .scanlines:after {
            top: 0;
            right: 0;
            bottom: 0;
            left: 0;
            z-index: 2147483648;
            background: -webkit-gradient(linear, left top, left bottom, color-stop(50%, transparent), color-stop(51%, rgba(0, 0, 0, 0.3)));
            background: linear-gradient(to bottom, transparent 50%, rgba(0, 0, 0, 0.3) 51%);
            background-size: 100% 4px;
            -webkit-animation: scanlines 1s steps(60) infinite;
            animation: scanlines 1s steps(60) infinite;
        }

        /* ANIMATE UNIQUE SCANLINE */
        @-webkit-keyframes scanline {
            0% {
                -webkit-transform: translate3d(0, 200000%, 0);
                transform: translate3d(0, 200000%, 0);
            }
        }
        @keyframes scanline {
            0% {
                -webkit-transform: translate3d(0, 200000%, 0);
                transform: translate3d(0, 200000%, 0);
            }
        }
        @-webkit-keyframes scanlines {
            0% {
                background-position: 0 50%;
            }
        }
        @keyframes scanlines {
            0% {
                background-position: 0 50%;
            }
        }
    </style>
</head>
"""  # noqa: E501

HOMEPAGE_BODY = r"""
<body onload="scanlines_init()">
    <main class="container">
        <code>
            Welcome to <span class="nicerbold">ihateani.me</span> simple BiliBili Scheduler API Endpoint
            <br>
            Created by <span class="nicerbold">N4O</span><br>
            Contact me at Discord: <span class="nicerbold">N4O#8868</span><br>
            <br>
            Current time: <span class="nicerbold" id="current_dt">Loading...</span><br>
            Detailed API Documentation<br>
            --&gt; <a href="/swagger">API Docs</a> (Swagger UI)<br>
            --&gt; <a href="/changelog">Website Changelog</a><br>
            <p>This API focus was for BiliBili but was improved to support Youtube channels as well.<br>
            Starting from <span class="nicerbold">version 0.8.5</span> this API support all Nijisanji VTubers that are on Youtube.<br>
            Including Nijisanji EN/ID/KR.<br><br>
            <span class="nicerbold">Please note</span>: Not all of the deployed code in this web are available in the source code.</p>
            <span class="nicerbold">Supported currently are:</span><br>
            - HoloLive JP/CN/ID<br>
            - Nijisanji JP/EN/ID/KR/CN<br>
            - <a href="/other">Other VTuber</a><br>
            <br>
            <span class="nicerbold">Endpoint:</span><br>
            <span class="nicerbold">&gt;&gt; Hololive &lt;&lt;</span><br>
            - <a href="/live">`/live`</a> for Hololivers Live/Upcoming Bili streams<br>
            - <a href="/channels">`/channels`</a> for Hololivers BiliBili channels stats<br>
            <br>
            <span class="nicerbold">&gt;&gt; Nijisanji &lt;&lt;</span><br>
            - <a href="/nijisanji/live">`/nijisanji/live`</a> for Nijisanji Live/Upcoming Bili
            streams<br>
            - <a href="/nijisanji/channels">`/nijisanji/channels`</a> for Nijisanji BiliBili channels
            stats<br>
            - <a href="/nijisanji/youtube/live">`/nijisanji/youtube/live`</a> for Nijisanji Live/Upcoming Youtube
            streams<br>
            - <a href="/nijisanji/youtube/channels">`/nijisanji/youtube/channels`</a> for Nijisanji Youtube channels
            stats<br>
            <br>
            <span class="nicerbold">&gt;&gt; Others &lt;&lt;</span><br>
            - <a href="/other/upcoming">`/other/upcoming`</a> for Other VTuber<br>
            - <a href="/other/channels">`/other/channels`</a> to check supported "Other VTuber"<br>
            - <a href="/other/youtube/live">`/other/youtube/live`</a> to see upcoming/live for some other
            vtuber.<br>
            - <a href="/other/youtube/channels">`/other/youtube/channels`</a> to see supported channels for
            youtube version of other vtuber.<br>
            <br>
            <span class="nicerbold">&gt;&gt; Others Platform &lt;&lt;</span><br>
            - <a href="/twitcasting/live">`/twitcasting/live`</a> for Twitcasting streams<br>
            - <a href="/twitcasting/channels">`/twitcasting/channels`</a> for Twitcaster channels
            stats<br>
            - <a href="/twitch/live">`/twitch/live`</a> for Twitch streams<br>
            - <a href="/twitch/channels">`/twitch/channels`</a> for Twitch channels stats<br>
            <br>
            <span class="nicerbold">Dataset Used:</span><br>
            - vtbs.moe<br>
            - <a href="https://github.com/noaione/vthell/tree/master/dataset">`vthell`</a> by N4O<br>
            <br>
            <span class="nicerbold">Refresh/Cache Rate:</span><br>
            - Channels: Every 6 hours<br>
            - Upcoming (Bili): Every 4 minutes<br>
            - Live (Bili): Every 2 minutes<br>
            - Upcoming (YT): Every 2 minutes<br>
            - Live (YT/Twitch/Twitcasting): Every 1 minute<br>
            <br>"""  # noqa: E501
HOMEPAGE_BODY_FMT = """
            <span class="nicerbold">Backend:</span><br>
            - Framework: Sanic v{sv} (Python {pyv})<br>
            - Database: MongoDB Community v{dbver}
            <br><br>
            <span class="nicerbold">&lt;/&gt;</span> Source Code: <a href="https://github.com/noaione/vtb-schedule">GitHub</a> <span class="nicerbold">&lt;/&gt;</span>
            <br>
            <span class="nicerbold">&lt;/&gt;</span> Deployed API <span class="nicerbold">v{appver}</span> <span class="nicerbold">&lt;/&gt;</span>
"""  # noqa: E501
HOMEPAGE_BODY_END = r"""
            <br>
            <br>
            <a style="cursor: pointer;" onclick="toggleScanlines()"><span class="nicerbold">&lt;/&gt;</span> Toggle Scanlines FX <span class="nicerbold">&lt;/&gt;</span></a>
        </code>
    </main>
    <script>
        function scanlines_init() {
            var scansData = localStorage.getItem("enableScan");
            if (scansData == null) {
                localStorage.setItem("enableScan", 1);
            };
            var scansData = localStorage.getItem("enableScan");
            console.log(scansData);
            if (scansData == 0) {
                console.log("removing")
                document.body.classList.remove("scanlines");
            } else {
                if (!document.body.classList.contains("scanlines")) {
                    document.body.classList.add("scanlines");
                };
            };
        }
        function getLocale() {
            return ( navigator.language || navigator.languages[0] );
        }
        var locale = getLocale();
        function getJPTime() {
            var local_time = new Date();
            return local_time.toLocaleString(
                locale, {
                    year: "numeric",
                    month: "short",
                    day: "2-digit",
                    hour: "numeric",
                    hour12: false,
                    minute: "numeric",
                    second: "numeric",
                    timeZone: "Asia/Tokyo",
                    weekday: "short"
                }
            ).replace(/, /g, " ") + " JST";
        }

        const clock = document.getElementById("current_dt");
        clock.textContent = getJPTime();
        setInterval(function () {
                clock.textContent = getJPTime();
            },
            1000
        );

        function toggleScanlines() {
            if (!document.body.classList.contains("scanlines")) {
                document.body.classList.add("scanlines");
                localStorage.setItem("enableScan", 1);
            } else {
                document.body.classList.remove("scanlines");
                localStorage.setItem("enableScan", 0);
            }
        }
    </script>
</body>
</html>
"""  # noqa: E501


@app.exception(NotFound)
async def handle_404(request, exception):
    logger.warning(f"URL {request.path} not found, sending current UTC Time...")
    current_time = int(round(datetime.now(tz=pytz.timezone("UTC")).timestamp()))
    return json({"time": current_time}, status=404)


@app.middleware("response")
async def before_response(request, response):
    response.headers["server-backend"] = "Sanic-{}".format(sanicver)
    response.headers["server-api-version"] = app.config.get("API_VERSION", "UNKNOWN")
    response.headers["x-xss-protection"] = "1; mode=block"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, HEAD"  # noqa: E501


logger.info("Adding routes...")
app.blueprint(holobp)
app.blueprint(nijibp)
app.blueprint(otherbp)
app.blueprint(twitcastbp)
app.blueprint(twitchbp)
app.blueprint(changebp)


@app.get("/other/yt/live")
@doc.exclude(True)
async def live_other_yt_old_route(request):
    return redirect("/other/youtube/live")


@app.get("/other/yt/channels")
@doc.exclude(True)
async def channels_other_yt_old_route(request):
    return redirect("/other/youtube/channels")


app.static("/other", "./static/othervt.html", content_type="text/html; charset=utf-8")

app.static("/favicon.ico", "./static/ihaBadge.ico", content_type="image/x-icon")
app.static("/favicon.png", "./static/ihaBadge.png", content_type="image/png")


@app.route("/")
@doc.exclude(True)
async def home(request):
    pyver = "{0.major}.{0.minor}.{0.micro}".format(sys.version_info)
    app_ver = request.app.config["API_VERSION"]
    db_ver = request.app.config["MONGODB_DBVERSION"]
    html_text = (
        HOMEPAGE_HEADERS
        + HOMEPAGE_BODY
        + HOMEPAGE_BODY_FMT.format(sv=sanicver, pyv=pyver, appver=app_ver, dbver=db_ver)
        + HOMEPAGE_BODY_END
    )
    return html(html_text)


ROBOTS_TXTS = """User-agent: *
Disallow: /live
Disallow: /channels
Disallow: /parrot
Disallow: /bilihls
Disallow: /ping
Disallow: /nijisanji/*
Disallow: /other/*
Disallow: /u2/*
Disallow: /twitcasting/*
Disallow: /twitch/*"""


@app.route("/robots.txt")
@doc.exclude(True)
async def robotstxt(request):
    return text(ROBOTS_TXTS)


if __name__ == "__main__":
    logger.info("Starting server...")
    app.run(host="127.0.0.1", port=8000, debug=False, access_log=True)
