# VTBili Schedule (Web Server)

Frontend of the VTBili Schedule program.

## Initializing
1. Install all requirements
2. Install memcached and run it in background/daemon.
3. Open `app.py`

Modify some of this part:
```py
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
    API_LICENSE_URL="https://github.com/noaione/vthell/blob/master/LICENSE"
)
```
Change `MOTOR_URI` to your mongodb URL + database name (default: vtbili)<br>
Change `MEMCACHED_HOST` and `MEMCACHED_PORT` to your IP/PORT.<br>
Change `API_MASTER_KEY` to something random that you can remember.<br>
Change `APP_EXCLUDE_IPS_LIMIT` if you want.<br>
Change `APP_IMPLEMENT_RATE_LIMIT` if you want to enable Rate Limiting.

## Running
Just run `app.py`
```sh
python3 app.py
```