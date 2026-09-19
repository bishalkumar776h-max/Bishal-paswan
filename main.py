# bishalpaswanbot CORE ON TOP BABY !!!
# AUTO-REGION FINDER INFO API
# FULLY FIXED FOR ALL PLATFORMS
# NO API KEY REQUIRED
# JOIN @bishalpaswanbot FOR MORE LEAKS

import asyncio
import time
import httpx
import json
import random
import threading
import os
import sys
import base64
from collections import defaultdict
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from cachetools import TTLCache
from typing import Tuple, Optional
from proto import FreeFire_pb2, main_pb2, AccountPersonalShow_pb2
from google.protobuf import json_format, message
from google.protobuf.message import Message
from Crypto.Cipher import AES
import logging

# ---------- Logging Setup ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- Config ----------
MAIN_KEY = base64.b64decode('WWcmdGMlREV1aDYlWmNeOA==')
MAIN_IV = base64.b64decode('Nm95WkRyMjJFM3ljaGpNJQ==')
RELEASEVERSION = "OB55"
USERAGENT = "Dalvik/2.1.0 (Linux; U; Android 13; CPH2095 Build/RKQ1.211119.001)"
SUPPORTED_REGIONS = [
    "IND", "SG", "ID", "BR", "VN", "US", "SAC", "NA",
    "RU", "TH", "TW", "BD", "PK", "ME", "CIS", "EUROPE"
]

# ---------- JWT API (NEW) ----------
JWT_API_URL = "https://bishal-jwt-api.vercel.app/token"

# Region -> server URL mapping (JWT API server URL nahi deti)
REGION_SERVER_URLS = {
    "IND":    "https://client.ind.freefiremobile.com",
    "BD":     "https://clientbp.ppmainecoonghj.com",
    "ME":     "https://clientbp.ppmainecoonghj.com",
    "BR":     "https://client.us.freefiremobile.com",
    "US":     "https://client.us.freefiremobile.com",
    "SAC":    "https://client.us.freefiremobile.com",
    "NA":     "https://client.us.freefiremobile.com",
    "SG":     "https://client.sg.freefiremobile.com",
    "ID":     "https://client.id.freefiremobile.com",
    "VN":     "https://client.vn.freefiremobile.com",
    "TH":     "https://client.th.freefiremobile.com",
    "TW":     "https://client.tw.freefiremobile.com",
    "PK":     "https://client.pk.freefiremobile.com",
    "RU":     "https://client.ru.freefiremobile.com",
    "CIS":    "https://client.cis.freefiremobile.com",
    "EUROPE": "https://client.eu.freefiremobile.com",
}

# ---------- App Setup ----------
app = Flask(__name__)
CORS(app)
cache = TTLCache(maxsize=200, ttl=600)
uid_region_cache = TTLCache(maxsize=200, ttl=3600)
cached_tokens = defaultdict(dict)

# Shared HTTP client (perf fix)
_http: Optional[httpx.AsyncClient] = None
def http() -> httpx.AsyncClient:
    global _http
    if _http is None:
        _http = httpx.AsyncClient(
            timeout=httpx.Timeout(20.0, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
        )
    return _http

# ---------- Helper Functions ------------
def pad(text: bytes) -> bytes:
    padding_length = AES.block_size - (len(text) % AES.block_size)
    return text + bytes([padding_length] * padding_length)

def aes_cbc_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    aes = AES.new(key, AES.MODE_CBC, iv)
    return aes.encrypt(pad(plaintext))

def decode_protobuf(encoded_data: bytes, message_type: message.Message) -> message.Message:
    instance = message_type()
    try:
        instance.ParseFromString(encoded_data)
        return instance
    except Exception as e:
        logger.error(f"Protobuf decode error: {e}")
        return None

async def json_to_proto(json_data: str, proto_message: Message) -> bytes:
    json_format.ParseDict(json.loads(json_data), proto_message)
    return proto_message.SerializeToString()

# ---------- Guest IDS (UNCHANGED) --------------
def get_account_credentials(region: str) -> str:
    r = region.upper()

    credentials = {
        "IND": "uid=4587290647&password=BUNNY_FLASH_SBQ8W",
        "BR": "uid=4519662843&password=BUNNYXPRIMEFF6ZR7G",
        "US": "uid=4519662843&password=BUNNYXPRIMEFF6ZR7G",
        "SAC": "uid=4519662843&password=BUNNYXPRIMEFF6ZR7G",
        "NA": "uid=4519662843&password=BUNNYXPRIMEFF6ZR7G",
        "VN": "uid=4626121698&password=BUNNYXPRIMEFFX7SKY",
        "SG": "uid=4626121698&password=BUNNYXPRIMEFFX7SKY",
        "ID": "uid=4519662843&password=BUNNYXPRIMEFF6ZR7G",
        "TH": "uid=4626121698&password=BUNNYXPRIMEFFX7SKY",
        "TW": "uid=4626121698&password=BUNNYXPRIMEFFX7SKY",
        "BD": "uid=4270765241&password=CKR_DSL17_BY_SPIDEERIO_GAMING_JTUB1",
        "PK": "uid=4519662843&password=BUNNYXPRIMEFF6ZR7G",
        "ME": "uid=4626121698&password=BUNNYXPRIMEFFX7SKY",
        "RU": "uid=4519662843&password=BUNNYXPRIMEFF6ZR7G",
        "CIS": "uid=4519662843&password=BUNNYXPRIMEFF6ZR7G",
        "EUROPE": "uid=4626121698&password=BUNNYXPRIMEFFX7SKY"
    }

    if r in credentials:
        return credentials[r]

    # Fallback to file
    try:
        with open("ucguest.txt", "r") as f:
            lines = [line.strip() for line in f if line.strip()]
            if not lines:
                raise ValueError("ucguest.txt is empty")
            uid, password = random.choice(lines).split()
            return f"uid={uid}&password={password}"
    except Exception as e:
        logger.error(f"Guest file error: {e}")
        return "uid=4587290647&password=BUNNY_FLASH_SBQ8W"

def _parse_uid_pw(region: str) -> Tuple[Optional[str], Optional[str]]:
    """'uid=X&password=Y' -> ('X', 'Y')"""
    raw = get_account_credentials(region)
    try:
        parts = dict(p.split("=", 1) for p in raw.split("&"))
        return parts.get("uid"), parts.get("password")
    except Exception:
        return None, None

# ---------- JWT payload helpers (NEW) ----------
def _region_from_jwt(tok: str) -> Optional[str]:
    """Decode JWT payload (no verify) and read lock_region."""
    try:
        parts = tok.split(".")
        if len(parts) < 2:
            return None
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get("lock_region") or payload.get("noti_region")
    except Exception:
        return None

# ---------- JWT API call (NEW) ----------
async def get_jwt_token_from_api(region: str) -> Optional[dict]:
    uid, pw = _parse_uid_pw(region)
    if not uid or not pw or pw == "ADD_HERE":
        logger.debug(f"[JWT] {region}: no valid creds")
        return None

    url = f"{JWT_API_URL}?uid={uid}&password={pw}"
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

    try:
        r = await http().get(url, headers=headers)
        logger.info(f"[JWT] {region} HTTP {r.status_code} body={r.text[:140]!r}")
        if r.status_code != 200:
            return None
        data = r.json()
    except Exception as e:
        logger.error(f"⚠️ JWT API {region}: {e}")
        return None

    tok = data.get("token")
    if not tok:
        logger.error(f"[JWT] {region} no 'token' in response: {data}")
        return None

    # Region: JWT payload se, warna requested region
    api_region = _region_from_jwt(tok) or region
    server_url = REGION_SERVER_URLS.get(api_region, "https://clientbp.ppmainecoonghj.com")

    return {
        "token": f"Bearer {tok}",
        "region": api_region,
        "server_url": server_url,
        "expires_at": time.time() + 25200,
    }

# -------------- Token Generation (MajorLogin fallback) --------------
async def get_access_token(account: str, timeout: int = 15):
    url = "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant"
    payload = f"{account}&response_type=token&client_type=2&client_secret=2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3&client_id=100067"
    headers = {
        'User-Agent': USERAGENT,
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/x-www-form-urlencoded"
    }

    try:
        r = await http().post(url, data=payload, headers=headers)
        if r.status_code != 200:
            logger.error(f"Access token failed: {r.status_code}")
            return "0", "0"
        data = r.json()
        return data.get("access_token", "0"), data.get("open_id", "0")
    except Exception as e:
        logger.error(f"Access token error: {e}")
        return "0", "0"

async def create_jwt(region: str):
    """MajorLogin fallback (purana tarika)."""
    try:
        account = get_account_credentials(region)
        token_val, open_id = await get_access_token(account)

        if token_val == "0" or open_id == "0":
            logger.error(f"Invalid token/open_id for {region}")
            return

        body = json.dumps({
            "open_id": open_id,
            "open_id_type": "4",
            "login_token": token_val,
            "orign_platform_type": "4"
        })

        proto_bytes = await json_to_proto(body, FreeFire_pb2.LoginReq())
        payload = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, proto_bytes)

        url = "https://loginbp.ppmainecoonghj.com"
        headers = {
            'User-Agent': USERAGENT,
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'Content-Type': "application/octet-stream",
            'Expect': "100-continue",
            'X-Unity-Version': "2018.4.11f1",
            'X-GA': "v1 1",
            'ReleaseVersion': RELEASEVERSION
        }

        r = await http().post(url, data=payload, headers=headers)

        ctype = r.headers.get("content-type", "")
        if r.status_code != 200 or "text/" in ctype:
            logger.warning(f"MajorLogin {region}: HTTP {r.status_code} ct={ctype} "
                           f"body={r.text[:80]!r}")
            return

        decoded = decode_protobuf(r.content, FreeFire_pb2.LoginRes)
        if not decoded:
            return

        msg = json.loads(json_format.MessageToJson(decoded))

        cached_tokens[region] = {
            'token': f"Bearer {msg.get('token','0')}",
            'region': msg.get('lockRegion','0'),
            'server_url': msg.get('serverUrl','0'),
            'expires_at': time.time() + 25200
        }

        logger.info(f"✅ MajorLogin Token OK [{region}]")
    except Exception as e:
        logger.error(f"Error creating JWT for {region}: {e}")

# ---------- Token flow (NEW: JWT first, MajorLogin fallback) ----------
async def get_token_info(region: str) -> Tuple[str, str, str]:
    info = cached_tokens.get(region)
    if info and time.time() < info.get('expires_at', 0):
        return info['token'], info['region'], info['server_url']

    # 1) JWT API (primary)
    info = await get_jwt_token_from_api(region)

    # 2) MajorLogin fallback
    if not info:
        await create_jwt(region)
        info = cached_tokens.get(region)

    if not info:
        raise RuntimeError(f"No token available for {region}")

    cached_tokens[region] = info
    return info['token'], info['region'], info['server_url']

async def initialize_tokens():
    logger.info("Initializing tokens for all regions...")
    tasks = [get_token_info(r) for r in SUPPORTED_REGIONS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for region, res in zip(SUPPORTED_REGIONS, results):
        if isinstance(res, Exception):
            logger.error(f"[startup] {region}: {res}")

async def refresh_tokens_periodically():
    while True:
        await asyncio.sleep(25200)
        await initialize_tokens()

# ---------- Get Account Information (mostly unchanged) ----------
async def GetAccountInformation(uid, unk, region, endpoint):
    try:
        payload = await json_to_proto(
            json.dumps({'a': uid, 'b': unk}),
            main_pb2.GetPlayerPersonalShow()
        )

        data_enc = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, payload)
        token, lock, server = await get_token_info(region)

        headers = {
            'User-Agent': USERAGENT,
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'Content-Type': "application/octet-stream",
            'Expect': "100-continue",
            'Authorization': token,
            'X-Unity-Version': "2018.4.11f1",
            'X-GA': "v1 1",
            'ReleaseVersion': RELEASEVERSION
        }

        r = await http().post(server + endpoint, data=data_enc, headers=headers)

        if r.status_code != 200:
            logger.error(f"Account info failed: {r.status_code} region={region}")
            return None
        if "text/" in r.headers.get("content-type", ""):
            return None

        decoded = decode_protobuf(r.content, AccountPersonalShow_pb2.AccountPersonalShowInfo)
        if not decoded:
            return None

        return json.loads(json_format.MessageToJson(decoded))
    except Exception as e:
        logger.error(f"GetAccountInformation error: {e}")
        return None

# -------------- Cache Decorator (unchanged) --------------
def cached_endpoint(ttl=300):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*a, **k):
            key = (request.path, tuple(request.args.items()))
            if key in cache:
                return cache[key]

            res = fn(*a, **k)
            cache[key] = res
            return res

        return wrapper
    return decorator

# -------------- Routes (unchanged) --------------
@app.route('/bmw', methods=['GET'])
@cached_endpoint()
def get_account_info():
    """Main endpoint: /bmw?uid=123456789"""
    uid = request.args.get('uid')

    if not uid:
        return jsonify({"error": "Please provide UID. Usage: /bmw?uid=123456789"}), 400

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if uid in uid_region_cache:
        try:
            data = loop.run_until_complete(
                GetAccountInformation(uid, "7", uid_region_cache[uid], "/GetPlayerPersonalShow")
            )
            if data:
                return jsonify(data)
        except Exception as e:
            logger.error(f"Cached region failed: {e}")

    for region in SUPPORTED_REGIONS:
        try:
            data = loop.run_until_complete(
                GetAccountInformation(uid, "7", region, "/GetPlayerPersonalShow")
            )

            if data:
                uid_region_cache[uid] = region
                return jsonify(data)
        except Exception as e:
            logger.debug(f"Region {region} failed for UID {uid}: {e}")
            continue

    return jsonify({"error": "UID not found or account doesn't exist"}), 404

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "active",
        "regions": len(SUPPORTED_REGIONS),
        "cached_tokens": len(cached_tokens),
        "cache_size": len(cache)
    }), 200

@app.route('/refresh-tokens', methods=['GET', 'POST'])
def refresh_tokens_endpoint():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(initialize_tokens())
        return jsonify({'message': 'Tokens refreshed successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "name": "FreeFire Auto-Region Finder API",
        "version": "2.1",
        "endpoints": {
            "/bmw": "Get account info - Usage: /bmw?uid=123456789",
            "/health": "Health check",
            "/refresh-tokens": "Force refresh tokens"
        },
        "status": "running"
    }), 200

# -------------- Error Handlers --------------
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# -------------- Async Startup --------------
started = False

def start_background_loop():
    global started
    if started:
        return
    started = True

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(initialize_tokens())
        loop.create_task(refresh_tokens_periodically())
        loop.run_forever()
    except Exception as e:
        logger.error(f"Background loop error: {e}")

def run_flask():
    port = int(os.environ.get('PORT', 5000))

    if os.environ.get('RENDER') or os.environ.get('VERCEL'):
        host = '0.0.0.0'
    else:
        host = '0.0.0.0'

    thread = threading.Thread(target=start_background_loop, daemon=True)
    thread.start()

    app.run(host=host, port=port, debug=False, threaded=True)

if __name__ == '__main__':
    if os.environ.get('VERCEL'):
        app.config['ENV'] = 'production'
        app.config['DEBUG'] = False
        threading.Thread(target=start_background_loop, daemon=True).start()
    else:
        run_flask()