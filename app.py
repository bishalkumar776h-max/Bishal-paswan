import asyncio
import time
import httpx
import json
import os
import base64
from collections import defaultdict
from flask import Flask, request, jsonify
from flask_cors import CORS
from cachetools import TTLCache
from typing import Tuple
from google.protobuf import json_format, message
from google.protobuf.message import Message
from Crypto.Cipher import AES
import sys

# Proto import fix
current_dir = os.path.dirname(os.path.abspath(__file__))
proto_dir = os.path.join(current_dir, 'proto')
if proto_dir not in sys.path:
    sys.path.insert(0, proto_dir)

try:
    from proto import FreeFire_pb2, main_pb2, AccountPersonalShow_pb2
    print("✅ Proto files imported successfully")
except ImportError:
    try:
        import FreeFire_pb2, main_pb2, AccountPersonalShow_pb2
        print("✅ Proto files imported directly")
    except ImportError as e:
        print(f"❌ Proto import error: {e}")
        sys.exit(1)

# === Settings ===
MAIN_KEY = base64.b64decode('WWcmdGMlREV1aDYlWmNeOA==')
MAIN_IV = base64.b64decode('Nm95WkRyMjJFM3ljaGpNJQ==')
RELEASEVERSION = "OB54"
USERAGENT = "Dalvik/2.1.0 (Linux; U; Android 13; CPH2095 Build/RKQ1.211119.001)"

# === Region Server URL Mapping ===
SERVER_URLS = {
    "ME": "https://clientbp.ggpolarbear.com",
    "BD": "https://clientbp.ggpolarbear.com",
    "IND": "https://client.ind.freefiremobile.com"
}

REGION_PRIORITY = ["ME", "BD", "IND"]

# === Account Credentials (From JSON files) ===
# IND Region Accounts
ACCOUNT_CREDENTIALS = {
    "ME": [
        {"uid": "4269012488", "password": "MG24_GAMER_U27YB_BY_SPIDEERIO_GAMING_0PNCN"},
        {"uid": "4269012487", "password": "MG24_GAMER_8WIUT_BY_SPIDEERIO_GAMING_Z11UK"},
        {"uid": "4269012497", "password": "MG24_GAMER_1Y4RE_BY_SPIDEERIO_GAMING_T2U2V"},
    ],
    "BD": [
        {"uid": "5541946315", "password": "MARUF_PXKV"},
        {"uid": "4270778393", "password": "MG24_GAMER_9NMYG_BY_SPIDEERIO_GAMING_FXK8R"},
    ],
    "IND": [
        {"uid": "5588213371", "password": "3AC9EA5DA08B25D11BBA8D372BC1C3FDDD6351BDED6C533440497AAB6FB0A3A2"},
        {"uid": "5588213780", "password": "BA7BDD6C25341D7D0E513F7E32F075BD31C2C4DD703626762C4EFCAFD03DF39C"},
        {"uid": "5588213833", "password": "6CB56657E1CCC94D2CF57923408FF0AAEC7CF4CE332F388802AB2C4345E4C6E4"},
        {"uid": "5588213782", "password": "84937242CAD0E431864B0AE01F2519D61E6798EC2EFA59741B70EDB5636931E7"},
        {"uid": "5588213464", "password": "1914E53D99DB6C3986B26BA736C8BC73F82634249B330C886B402761BE77CBB5"},
        {"uid": "5588212657", "password": "CBC66D76042F0875FB4C3EAB99B1FCA580CB329D85BE16B266968FD5DDDD2BA5"},
        {"uid": "5588213541", "password": "AFD4C542893FA4A3246CD381A815223842FD4175A2BBB2B2DC23527CFEBC8A79"},
        {"uid": "5588213153", "password": "B61BC54C7E1183B39DD5A3A9A54F3D23FA65C27E05F073CEAA6598EFBB27C943"},
        {"uid": "5588213680", "password": "146B0A5D0A03927D977AB07CD3C65E75DDC4DA0CFA54944D97FF50B4CAC209A7"},
        {"uid": "5588213772", "password": "2E46B2B57114366DDBF25319493073E00DB8F8A540B20E87C8719D2678CF0DB6"},
        {"uid": "5588213718", "password": "0A66B80C3D491384C73519926F446C701DF585471235F127E5A6ABE9754EA443"},
    ]
}

current_account_index = {"ME": 0, "BD": 0, "IND": 0}

# === Flask App Setup ===
app = Flask(__name__)
CORS(app)
cache = TTLCache(maxsize=100, ttl=300)
cached_tokens = defaultdict(dict)

# === Helper Functions ===
def pad(text: bytes) -> bytes:
    padding_length = AES.block_size - (len(text) % AES.block_size)
    return text + bytes([padding_length] * padding_length)

def aes_cbc_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    aes = AES.new(key, AES.MODE_CBC, iv)
    return aes.encrypt(pad(plaintext))

async def json_to_proto(json_data: str, proto_message: Message) -> bytes:
    json_format.ParseDict(json.loads(json_data), proto_message)
    return proto_message.SerializeToString()

# === Token Generation using URL ===
async def GeNeRaTeAccEss(uid, password):
    """Generate access token using external API"""
    TOKEN_URL = f"https://token.killersharmabot.online/token?uid={uid}&password={password}"
    
    try:
        print(f"🔑 Requesting token from: {TOKEN_URL}")
        
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            response = await client.get(TOKEN_URL)
            
            print(f"📡 Token API Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"📦 Token API Response: {json.dumps(data, indent=2)}")
                    
                    # Check if we have access_token and open_id directly
                    access_token = data.get("access_token")
                    open_id = data.get("open_id")
                    
                    # Also check for token field
                    if not access_token:
                        access_token = data.get("token")
                    
                    if access_token and open_id:
                        print(f"✅ Token success for UID: {uid}")
                        return open_id, access_token, False
                    
                    # Check if it's in queue
                    if "queueInfo" in data:
                        print(f"⏳ Account {uid} is in queue")
                        return None, None, False
                    
                    # Check for error
                    error_msg = data.get("message", data.get("msg", "Unknown error"))
                    print(f"❌ API Error: {error_msg}")
                    
                    if "rate" in str(error_msg).lower() or "429" in str(error_msg):
                        return None, None, True
                    
                    return None, None, False
                        
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON response: {response.text[:200]}")
                    return None, None, False
                    
            elif response.status_code == 429:
                print(f"❌ Rate Limited for UID: {uid}")
                return None, None, True
            else:
                print(f"❌ HTTP Error: {response.status_code} for UID: {uid}")
                print(f"Response: {response.text[:200]}")
                return None, None, False
                
    except Exception as e:
        print(f"❌ Error generating token: {e}")
        return None, None, False

# === MajorLogin ===
async def EncRypTMajoRLoGin(open_id, access_token):
    """Create MajorLogin request"""
    major_login = FreeFire_pb2.LoginReq()
    
    major_login.open_id = open_id
    major_login.open_id_type = "4"
    major_login.login_token = access_token
    major_login.orign_platform_type = "4"
    
    string = major_login.SerializeToString()
    return aes_cbc_encrypt(MAIN_KEY, MAIN_IV, string)

async def MajorLogin(payload):
    """Send MajorLogin request"""
    url = "https://loginbp.ggpolarbear.com/MajorLogin"
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
    
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        resp = await client.post(url, data=payload, headers=headers)
        if resp.status_code == 200:
            return resp.content
        print(f"❌ MajorLogin status: {resp.status_code}")
        return None

async def DecRypTMajoRLoGin(response_data):
    """Decrypt MajorLogin response"""
    proto = FreeFire_pb2.LoginRes()
    proto.ParseFromString(response_data)
    return proto

# === Create JWT ===
async def create_jwt(region: str):
    global current_account_index
    
    try:
        print(f"🔄 Creating JWT for {region}...")
        
        accounts = ACCOUNT_CREDENTIALS.get(region.upper(), [])
        if not accounts:
            print(f"❌ No credentials for {region}")
            return False
        
        start_index = current_account_index.get(region, 0)
        
        for i in range(len(accounts)):
            idx = (start_index + i) % len(accounts)
            creds = accounts[idx]
            uid = creds["uid"]
            password = creds["password"]
            
            print(f"   Trying account {idx+1}/{len(accounts)}: UID {uid}")
            
            open_id, access_token, rate_limited = await GeNeRaTeAccEss(uid, password)
            
            if rate_limited:
                print(f"   ⚠️ Account {uid} is rate limited, trying next...")
                continue
                
            if not open_id or not access_token:
                print(f"   ❌ Failed to get access token for UID {uid}")
                continue

            # Create MajorLogin request
            payload = await EncRypTMajoRLoGin(open_id, access_token)
            response = await MajorLogin(payload)
            
            if not response:
                print(f"   ❌ MajorLogin failed for UID {uid}")
                continue
                
            # Decrypt response
            login_res = await DecRypTMajoRLoGin(response)
            msg = json.loads(json_format.MessageToJson(login_res))
            
            print(f"   📦 Login response: {json.dumps(msg, indent=2)}")
            
            # Check if we got token
            if 'token' in msg and msg['token'] != '0' and msg['token'] != '':
                token = msg['token']
                server_url = msg.get('serverUrl', '0')
                
                if server_url == '0' or not server_url:
                    server_url = SERVER_URLS.get(region.upper(), "https://clientbp.ggpolarbear.com")
                elif not server_url.startswith(('http://', 'https://')):
                    server_url = 'https://' + server_url
                
                cached_tokens[region] = {
                    'token': f"Bearer {token}",
                    'region': msg.get('lockRegion', region),
                    'server_url': server_url,
                    'expires_at': time.time() + 25200,
                    'account_uid': uid
                }
                
                current_account_index[region] = idx
                
                print(f"✅ Token generated for {region} using UID {uid}")
                print(f"   Token: {token[:30]}...")
                print(f"   Server URL: {server_url}")
                return True
                
            elif 'queueInfo' in msg:
                print(f"   ⏳ Account {uid} in queue, trying next...")
                continue
            else:
                print(f"   ❌ Unexpected response for UID {uid}")
                continue
        
        print(f"❌ All accounts failed for {region}")
        return False

    except Exception as e:
        print(f"❌ Error creating JWT for {region}: {e}")
        import traceback
        traceback.print_exc()
        return False

async def get_token_info(region: str) -> Tuple[str, str, str]:
    info = cached_tokens.get(region)
    if info and time.time() < info['expires_at']:
        return info['token'], info['region'], info['server_url']
    
    print(f"🔄 Token expired or missing for {region}, regenerating...")
    success = await create_jwt(region)
    if not success:
        return None, None, None
    
    info = cached_tokens[region]
    return info['token'], info['region'], info['server_url']

# === Account Information ===
async def GetAccountInformation(uid, unk, region):
    try:
        token, lock, server_url = await get_token_info(region)
        if not token:
            print(f"❌ No token for {region}")
            return None

        if server_url and not server_url.startswith(('http://', 'https://')):
            server_url = 'https://' + server_url

        payload = await json_to_proto(
            json.dumps({'a': uid, 'b': unk}), 
            main_pb2.GetPlayerPersonalShow()
        )
        data_enc = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, payload)

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

        full_url = f"{server_url}/GetPlayerPersonalShow"
        print(f"🌐 Requesting: {full_url}")

        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            resp = await client.post(full_url, data=data_enc, headers=headers)
            
            if resp.status_code != 200:
                print(f"❌ API returned {resp.status_code} for {region}")
                return None

            account_info = AccountPersonalShow_pb2.AccountPersonalShowInfo()
            account_info.ParseFromString(resp.content)
            result = json.loads(json_format.MessageToJson(account_info))
            
            if result.get('basicInfo', {}).get('nickname'):
                print(f"✅ Info received for UID {uid} from {region}")
                return result
            else:
                print(f"⚠️ No player found for UID {uid} in {region}")
                return None

    except Exception as e:
        print(f"❌ GetAccountInformation error for {region}: {e}")
        return None

def format_response(data):
    if not data:
        return {"error": "No data"}
    
    basic = data.get("basicInfo", {})
    clan = data.get("clanBasicInfo", {})
    profile = data.get("profileInfo", {})
    
    return {
        "AccountInfo": {
            "AccountAvatarId": basic.get("headPic"),
            "AccountBPBadges": basic.get("badgeCnt"),
            "AccountBPID": basic.get("badgeId"),
            "AccountBannerId": basic.get("bannerId"),
            "AccountCreateTime": basic.get("createAt"),
            "AccountEXP": basic.get("exp"),
            "AccountLastLogin": basic.get("lastLoginAt"),
            "AccountLevel": basic.get("level"),
            "AccountLikes": basic.get("liked"),
            "AccountName": basic.get("nickname"),
            "AccountRegion": basic.get("region"),
            "AccountSeasonId": basic.get("seasonId"),
            "AccountType": basic.get("accountType"),
            "BrMaxRank": basic.get("maxRank"),
            "BrRankPoint": basic.get("rankingPoints"),
            "CsMaxRank": basic.get("csMaxRank"),
            "CsRankPoint": basic.get("csRankingPoints"),
            "EquippedWeapon": basic.get("weaponSkinShows", []),
            "ReleaseVersion": basic.get("releaseVersion"),
            "ShowBrRank": basic.get("showBrRank"),
            "ShowCsRank": basic.get("showCsRank"),
            "Title": basic.get("title")
        },
        "AccountProfileInfo": {
            "EquippedOutfit": profile.get("clothes", []),
            "EquippedSkills": profile.get("equipedSkills", [])
        },
        "GuildInfo": {
            "GuildCapacity": clan.get("capacity"),
            "GuildID": str(clan.get("clanId") or ""),
            "GuildLevel": clan.get("clanLevel"),
            "GuildMember": clan.get("memberNum"),
            "GuildName": clan.get("clanName"),
            "GuildOwner": str(clan.get("captainId") or "")
        },
        "captainBasicInfo": data.get("captainBasicInfo", {}),
        "creditScoreInfo": data.get("creditScoreInfo", {}),
        "petInfo": data.get("petInfo", {}),
        "socialinfo": data.get("socialInfo", {})
    }

# === API Routes ===
@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "version": RELEASEVERSION,
        "regions": REGION_PRIORITY,
        "total_accounts": {
            "ME": len(ACCOUNT_CREDENTIALS.get("ME", [])),
            "BD": len(ACCOUNT_CREDENTIALS.get("BD", [])),
            "IND": len(ACCOUNT_CREDENTIALS.get("IND", []))
        },
        "endpoints": {
            "/get?uid=UID": "Get player information",
            "/refresh": "Refresh all tokens",
            "/regions": "List supported regions",
            "/accounts": "Show account status"
        }
    })

@app.route('/accounts')
def show_accounts():
    status = {}
    for region in REGION_PRIORITY:
        accounts = ACCOUNT_CREDENTIALS.get(region, [])
        status[region] = {
            "total_accounts": len(accounts),
            "current_index": current_account_index.get(region, 0),
            "accounts": [
                {
                    "uid": acc["uid"],
                    "has_token": region in cached_tokens and cached_tokens[region].get("account_uid") == acc["uid"]
                }
                for acc in accounts
            ]
        }
    return jsonify(status)

@app.route('/get')
async def get_account_info():
    uid = request.args.get('uid')
    if not uid:
        return jsonify({"error": "Please provide UID."}), 400

    print(f"🔍 Searching for UID: {uid}")

    for region in REGION_PRIORITY:
        print(f"\n📍 Trying region: {region}")
        try:
            data = await GetAccountInformation(uid, "7", region)
            if data:
                formatted = format_response(data)
                return jsonify(formatted), 200
        except Exception as e:
            print(f"❌ Error for {region}: {e}")
            continue

    return jsonify({
        "error": "Player not found. Please check UID and try again."
    }), 404

@app.route('/refresh')
async def refresh_tokens_endpoint():
    try:
        tasks = [create_jwt(r) for r in REGION_PRIORITY]
        results = await asyncio.gather(*tasks)
        success_count = sum(1 for r in results if r)
        return jsonify({
            'message': f'Tokens refreshed for {success_count}/{len(REGION_PRIORITY)} regions',
            'total': len(REGION_PRIORITY),
            'success': success_count
        }), 200
    except Exception as e:
        return jsonify({'error': f'Refresh failed: {str(e)}'}), 500

@app.route('/regions')
def get_regions():
    return jsonify({
        "supported_regions": list(SERVER_URLS.keys()),
        "priority_regions": REGION_PRIORITY,
        "server_urls": SERVER_URLS
    })

# === Startup ===
async def startup():
    print("🚀 Starting Free Fire Info API...")
    print(f"📊 Loaded Accounts:")
    print(f"   ME: {len(ACCOUNT_CREDENTIALS.get('ME', []))} accounts")
    print(f"   BD: {len(ACCOUNT_CREDENTIALS.get('BD', []))} accounts")
    print(f"   IND: {len(ACCOUNT_CREDENTIALS.get('IND', []))} accounts")
    print("🔄 Initializing tokens for priority regions...")
    tasks = [create_jwt(r) for r in REGION_PRIORITY]
    await asyncio.gather(*tasks)
    print("✅ Startup complete!")

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(startup())
    
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Server running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)