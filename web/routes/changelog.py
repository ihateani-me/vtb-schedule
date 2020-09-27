from sanic import Blueprint
from sanic.log import logger
from sanic.response import html, json
from sanic_openapi import doc

from utils import udumps

changebp = Blueprint("changelog", "/changelog", strict_slashes=False)
changelog_stuff = {
    "0.2": ["First public API release.", "Include only upcoming streams"],
    "0.3": [
        "Added channels support", "Implement Youtube endpoint for other VTubers", "Open sourced the code"
    ],
    "0.4": ["Added live data support for bilibili.", "Added Swagger for API Docs."],
    "0.5": [
        "Rework backend code to made it faster", "Rearrange frontend stuff", "Removed API rate limiting."
    ],
    "0.6": ["Added Twitch and Twitcasting endpoint."],
    "0.6.2": ["Code cleanup.", "Utilize browser caching a.k.a Cache-Control"],
    "0.7": [
        "Add viewers count.", "New and slick homepage (lmao)"
    ],
    "0.8": [
        "Full website rework", "Improve backend code to be faster",
    ],
    "0.8.5": [
        "Add full Nijisanji EN/JP/ID/KR support to the website",
    ],
    "0.8.6": [
        "Add past live stream array for Nijisanji and Others VTubers on Youtube.",
        "Added this changelog page.",
        "Improvise how backend works for Youtube streams.",
    ],
    "0.9.0": [
        "Add group fields to youtube livestream results",
        "Allow filtering what will be returned to user (for Youtube streams).",
    ]
}


HOMEPAGE_HEADERS = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <meta http-equiv=X-UA-Compatible content="IE=edge,chrome=1">
    <title>ihateanime API // Changelog</title>
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
<body onload="scanlines_init()">
    <main class="container">
        <code>
"""  # noqa: E501

HOMEPAGE_BODY_END = r"""
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
        const clock = document.getElementById("current_dt");
        clock.textContent = (new Date()).toString();
        setInterval(function () {
                clock.textContent = (new Date()).toString();
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


@changebp.route("/")
@doc.route(exclude=True)
@doc.tag("Hololive")
async def changelog_api(request):
    logger.info("Route /changelog")
    is_json = request.args.get("json", 0)
    if isinstance(is_json, str):
        try:
            is_json = int(is_json)
        except ValueError:
            is_json = 0
    if is_json >= 1:
        return json(changelog_stuff, dumps=udumps, indent=2)
    gen_text = HOMEPAGE_HEADERS
    gen_text += '<span class="nicerbold">Website Changelog</span><br>\n'
    for ver, changes in changelog_stuff.items():
        gen_text += f'<span class="nicerbold">&gt;&gt; v{ver} &lt;&lt;</span><br>\n'
        for change in changes:
            if not change.startswith("("):
                gen_text += "- "
            gen_text += change + "<br>\n"
        gen_text += "<br>\n"
    gen_text += HOMEPAGE_BODY_END
    return html(gen_text)
