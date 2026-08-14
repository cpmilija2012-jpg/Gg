#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPM2 Server Tool — Research Edition
====================================
Built from leaked CPM2 cloud function endpoints.

APPROACH:
  1. Login & load raw player record
  2. INSPECT the record structure (JSON dump) before any edits
  3. Use SERVER endpoints (BuyCar, CheckGarage, GetAllCars) instead of
     blindly writing to unknown fields.
  4. Only modify KNOWN fields: money, coin, Name, localID.

CPM2 Facts:
  • ~150-170 total cars (not 250)
  • Garage has 20 slots
  • Endpoints are v23_1 / v22_1 (different from CPM1)
  • Player record structure may differ from CPM1
"""

import asyncio
import aiohttp
import base64
import brotli
import hashlib
import json
import struct
import sys
import time
import zlib
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# ═══════════════════════════════════════════
#  ⚙️  CONFIG
# ═══════════════════════════════════════════

API_KEY = "AIzaSyCQDz9rgjgmvmFkvVfmvr2-7fT4tfrzRRQ"
BASE_URL = "https://europe-west1-cpm-2-7cea1.cloudfunctions.net"

# ═══════════════════════════════════════════
#  🌐 ENDPOINTS (from leak)
# ═══════════════════════════════════════════

EP = {
    # Auth
    "login":               f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}",
    "refresh":             f"https://securetoken.googleapis.com/v1/token?key={API_KEY}",

    # Player Data
    "get_player_records":  f"{BASE_URL}/GetPlayerRecords23_1",
    "save_player_records": f"{BASE_URL}/SavePlayerRecords23_1",
    "get_money":           f"{BASE_URL}/GetMoney23_1",
    "get_coins":           f"{BASE_URL}/GetCoins23_1",
    "buy_money":           f"{BASE_URL}/BuyMoney21_1",
    "buy_coins":           f"{BASE_URL}/BuyCoins21_1",
    "spend_coins":         f"{BASE_URL}/SpendCoins23_1",
    "save_wallet":         f"{BASE_URL}/SaveWalletData23_1",

    # Cars / Garage
    "get_all_cars":        f"{BASE_URL}/GetAllCars23_1",
    "get_car_price":       f"{BASE_URL}/GetCarPrice23_1",
    "buy_car":             f"{BASE_URL}/BuyCar23_1",
    "save_car":            f"{BASE_URL}/SaveCar23_1",
    "check_garage":        f"{BASE_URL}/CheckGarage23_1",
    "sell_garage":         f"{BASE_URL}/SellGarage23_1",
    "exchange_car_money":  f"{BASE_URL}/ExchangeCarForMoney23_1",
    "remove_car_db":       f"{BASE_URL}/RemoveCarFromDatabase23_1",
    "mp_sell_car":         f"{BASE_URL}/MPSellCar23_1",
    "mp_exchange_cars":    f"{BASE_URL}/MPExchangeCars23_1",
    "are_cars_desync":     f"{BASE_URL}/AreCarsDesynchronized23_1",

    # Inventory
    "save_engine_inv":     f"{BASE_URL}/SaveEngineInventory23_1",
    "save_parts_inv":      f"{BASE_URL}/SavePartsInventory23_1",
    "save_slots":          f"{BASE_URL}/SaveSlotsCollection23_1",
    "save_plate_vinyls":   f"{BASE_URL}/SavePlateVinyls23_1",

    # Social
    "save_friends":        f"{BASE_URL}/SaveFriends23_1",

    # Rating / Racing
    "set_user_rating":     f"{BASE_URL}/SetUserRating23_1",
    "get_user_rating":     f"{BASE_URL}/GetUserRatingCall23_1",
    "get_user_rating_22":  f"{BASE_URL}/GetUserRatingCall22_1",
    "validate_rank":       f"{BASE_URL}/ValidateRank23_1",
    "set_circuit_racing":  f"{BASE_URL}/SetCircuitRacing23_1",
    "set_drag_racing":     f"{BASE_URL}/SetDragRacing23_1",
    "get_circuit_token":   f"{BASE_URL}/GetCircuitRacingToken23_1",

    # Events / Tasks / Rewards
    "get_all_events":      f"{BASE_URL}/GetAllCurrentEvents23_1",
    "submit_event":        f"{BASE_URL}/SubmitEventRecord23_1",
    "claim_event_reward":  f"{BASE_URL}/ClaimEventReward23_1",
    "get_daily_task":      f"{BASE_URL}/GetDailyTaskCall23_1",
    "get_rewards":         f"{BASE_URL}/GetRewards23_1",
    "award_reward":        f"{BASE_URL}/AwardReward23_1",

    # Offers / Shop
    "get_offers":          f"{BASE_URL}/GetOffersForPlayer23_1",
    "get_offer_by_id":     f"{BASE_URL}/GetOfferByOfferId23_1",
    "check_offer_version": f"{BASE_URL}/CheckOfferVersion23_1",
    "purchase_iap":        f"{BASE_URL}/PurchaseInAppItem23_1",
    "restore_purchase":    f"{BASE_URL}/RestorePurchase23_1",
    "has_purchase_hist":   f"{BASE_URL}/HasPurchaseHistory23_1",

    # Misc
    "ping":                f"{BASE_URL}/Ping23_1",
    "get_user_conn":       f"{BASE_URL}/GetUserConnectionData23_1",
    "get_user_conn_22":    f"{BASE_URL}/GetUserConnectionData22_1",
}

GAME_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/json",
    "User-Agent": "UnityPlayer/2022.3.62f2 (UnityWebRequest/1.0, libcurl/8.10.1-DEV)",
    "X-Unity-Version": "2022.3.62f2",
}

# ═══════════════════════════════════════════
#  🔐 CRYPTO (CPM1-based, may differ in CPM2)
# ═══════════════════════════════════════════

def make_xor_key(uid: str) -> bytes:
    chars = list(uid)
    if len(chars) >= 9: chars[1], chars[8] = chars[8], chars[1]
    if len(chars) >= 3: chars.pop(2)
    if len(chars) >= 5: chars.append(chars[4])
    return "".join(chars).encode("utf-8")

def xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(data[i] ^ key[i % len(key)] for i in range(len(data)))

def decompress(data: bytes) -> Optional[bytes]:
    try: return brotli.decompress(data)
    except: pass
    try: return zlib.decompress(data, zlib.MAX_WBITS | 16)
    except: pass
    try: return zlib.decompress(data)
    except: pass
    return None

def decrypt_aes(data: bytes, key: bytes) -> Optional[bytes]:
    if not HAS_CRYPTO: return None
    try:
        cipher = AES.new(key[:16], AES.MODE_CBC, b"\x00" * 16)
        return unpad(cipher.decrypt(data), 16)
    except: return None

def _md5(t): return hashlib.md5(t.encode()).digest()
def _sha1(t): return hashlib.sha1(t.encode()).digest()[:16]

def build_aes_keys(uid, password=None, email=None):
    keys = [_md5("olzhas_carparking")]
    if password: keys += [_md5(password), _sha1(password)]
    if uid:      keys += [_md5(uid), _sha1(uid)]
    if email:    keys.append(_md5(email))
    return keys

# ═══════════════════════════════════════════
#  📖 READER / PARSER (CPM1-based)
# ═══════════════════════════════════════════

class Reader:
    def __init__(self, data):
        self.buf = data; self.pos = 0
    def has_bytes(self, n): return self.pos + n <= len(self.buf)
    def read_byte(self):
        if not self.has_bytes(1): return 0
        v = self.buf[self.pos]; self.pos += 1; return v
    def read_int(self):
        if not self.has_bytes(4): self.pos = len(self.buf); return 0
        v = struct.unpack_from("<i", self.buf, self.pos)[0]; self.pos += 4; return v
    def read_float(self):
        if not self.has_bytes(4): self.pos = len(self.buf); return 0.0
        v = struct.unpack_from("<f", self.buf, self.pos)[0]; self.pos += 4; return v
    def read_string(self):
        marker = self.read_int()
        if marker in (0, -1): return ""
        length = (-marker) - 1 if marker < -1 else marker
        if marker < -1: self.read_int()
        if length > 1_000_000: length = 1_000_000
        if not self.has_bytes(length): return ""
        text = self.buf[self.pos:self.pos + length].decode("utf-8", errors="replace")
        self.pos += length
        return text.replace("\x00", "").strip()
    def read_list(self, item_fn):
        count = self.read_int()
        if count <= 0 or count > 1_000_000: return []
        result = []
        for _ in range(count):
            if self.pos >= len(self.buf): break
            v = item_fn()
            if v is not None: result.append(v)
        return result
    def read_dict(self):
        count = self.read_int()
        if count <= 0 or count > 1_000_000: return {}
        d = {}
        for _ in range(count):
            if self.pos >= len(self.buf): break
            d[self.read_int()] = self.read_int()
        return d
    def read_equipment(self):
        if self.read_byte() == 0: return None
        return {
            "hair": self.read_list(self.read_int), "face": self.read_list(self.read_int),
            "beard": self.read_list(self.read_int), "cap": self.read_list(self.read_int),
            "mask": self.read_list(self.read_int), "top": self.read_list(self.read_int),
            "gloves": self.read_list(self.read_int), "bag": self.read_list(self.read_int),
            "pants": self.read_list(self.read_int), "shoes": self.read_list(self.read_int),
            "glasses": self.read_list(self.read_int),
            "SelectedEquipments": self.read_list(self.read_int),
            "Gender": self.read_int(),
        }

def parse_player(buf):
    r = Reader(buf)
    if r.read_byte() == 0: return None
    p = {}
    p["Name"] = r.read_string(); p["money"] = r.read_int()
    p["coin"] = r.read_int(); p["localID"] = r.read_string()
    p["boughtFsos"] = r.read_list(r.read_int)
    def read_friend():
        r.read_byte()
        return {"id": r.read_string(), "Name": r.read_string(), "accountID": r.read_string()}
    p["FriendsID"] = r.read_list(read_friend)
    p["LevelsDoneTime"] = r.read_list(r.read_float)
    p["floats"] = r.read_list(r.read_float)
    p["integers"] = r.read_list(r.read_int)
    p["fcar"] = r.read_list(r.read_int)
    p["favouriteWheels"] = r.read_list(r.read_int)
    p["favouriteVinyls"] = r.read_list(r.read_int)
    p["favouriteEmojis"] = r.read_list(r.read_int)
    p["personEquipmentsMale"] = r.read_equipment()
    p["personEquipmentsFemale"] = r.read_equipment()
    if r.read_byte() == 0:
        p["platesData"] = None
    else:
        def read_vinyl():
            r.read_byte()
            def rv(): return {"x": r.read_float(), "y": r.read_float(), "z": r.read_float()}
            return {"vectors": r.read_list(rv), "v": r.read_list(r.read_string),
                    "floats": r.read_list(r.read_float), "text": r.read_string()}
        def read_plate():
            r.read_byte()
            return {"plateId": r.read_int(), "frontCarId": r.read_int(),
                    "rearCarId": r.read_int(), "vinyls": r.read_list(read_vinyl)}
        p["platesData"] = {"allPlates": r.read_list(read_plate)}
    if r.read_byte() == 0:
        p["carIDnStatus"] = None
    else:
        p["carIDnStatus"] = {
            "carGeneratedIDs": r.read_list(r.read_string),
            "carStatus": r.read_list(r.read_int),
        }
    p["allData"] = r.read_string()
    p["flags"] = r.read_dict()
    p["animations"] = r.read_list(r.read_int)
    p["emojiPacks"] = r.read_list(r.read_int)
    p["wheels"] = r.read_list(r.read_int)
    p["boughtPoliceLights"] = r.read_list(r.read_int)
    p["boughtPoliceSirens"] = r.read_list(r.read_int)
    return p

def try_parse(buf):
    candidates = [buf]
    d1 = decompress(buf)
    if d1:
        candidates.append(d1)
        d2 = decompress(d1)
        if d2: candidates.append(d2)
    for c in candidates:
        if not c: continue
        if len(c) > 0 and c[0] in (17, 23, 24):
            try:
                p = parse_player(c)
                if p and p.get("Name") is not None: return p
            except: pass
        try:
            clean = c[3:] if (len(c) >= 3 and c[0] == 0xef and c[1] == 0xbb) else c
            if clean[0] == 123: return json.loads(clean.decode("utf-8"))
        except: pass
    return None

def decrypt_player_record(base64_text, uid, password=None, email=None):
    try: buf = base64.b64decode(base64_text)
    except: return {"success": False, "message": "Bad base64"}
    if len(buf) < 10: return {"success": False, "message": "Too small"}
    direct = try_parse(buf)
    if direct: return {"success": True, "record": direct}
    if uid:
        try:
            xp = xor_bytes(buf, make_xor_key(uid))
            d = decompress(xp)
            if d:
                p = try_parse(d)
                if p: return {"success": True, "record": p}
        except: pass
    for key in build_aes_keys(uid or "", password, email):
        plain = decrypt_aes(buf, key)
        if not plain: continue
        p = try_parse(plain)
        if p: return {"success": True, "record": p}
    return {"success": False, "message": "Could not decrypt"}

# ═══════════════════════════════════════════
#  🎮 CPM2 CLIENT
# ═══════════════════════════════════════════

class CPM2Client:
    def __init__(self):
        self.auth_token: Optional[str] = None
        self.email: Optional[str] = None
        self.password: Optional[str] = None
        self.firebase_uid: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.record: Dict[str, Any] = {}
        self.raw_record_b64: Optional[str] = None
        self.all_cars: List[Dict] = []
        self.garage_info: Dict[str, Any] = {}

    async def _post(self, url: str, payload: Dict, headers: Optional[Dict] = None) -> Optional[Dict]:
        h = {**GAME_HEADERS}
        if headers: h.update(headers)
        if self.auth_token:
            h["Authorization"] = f"Bearer {self.auth_token}"
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout, connector=aiohttp.TCPConnector(ssl=False)) as s:
                async with s.post(url, json=payload, headers=h) as r:
                    text = await r.text()
                    try: return json.loads(text)
                    except: return {"raw": text, "status": r.status}
        except Exception as e:
            print(f"[HTTP Error] {e}")
            return None

    async def login(self, email: str, password: str) -> Dict:
        self.email = email; self.password = password
        p = {"email": email, "password": password, "returnSecureToken": True, "clientType": "CLIENT_TYPE_ANDROID"}
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout, connector=aiohttp.TCPConnector(ssl=False)) as s:
                async with s.post(EP["login"], json=p, headers=GAME_HEADERS) as resp:
                    r = await resp.json(content_type=None)
        except Exception as e:
            return {"ok": False, "message": f"NETWORK_ERROR: {e}"}
        if "idToken" in r:
            self.auth_token = r["idToken"]
            self.refresh_token = r.get("refreshToken", "")
            self.firebase_uid = r.get("localId", "")
            return {"ok": True, "firebase_uid": self.firebase_uid}
        err = str(r.get("error", {}).get("message", "")).upper()
        return {"ok": False, "message": err}

    async def refresh(self) -> bool:
        if not self.refresh_token:
            if self.email and self.password:
                r = await self.login(self.email, self.password)
                return r.get("ok", False)
            return False
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout, connector=aiohttp.TCPConnector(ssl=False)) as s:
                async with s.post(EP["refresh"], json={"grant_type":"refresh_token","refresh_token":self.refresh_token},
                                  headers={"Content-Type":"application/json"}) as resp:
                    r = await resp.json(content_type=None)
                    if r and r.get("id_token"):
                        self.auth_token = r["id_token"]
                        self.refresh_token = r.get("refresh_token", self.refresh_token)
                        return True
        except: pass
        if self.email and self.password:
            r = await self.login(self.email, self.password)
            return r.get("ok", False)
        return False

    # ── Player Data ─────────────────────────
    async def load_player(self) -> Dict:
        r = await self._post(EP["get_player_records"], {"data": None})
        if not r:
            return {"ok": False, "message": "No response", "raw": None}
        # Debug: save raw response
        self._last_raw_response = r
        if "result" not in r:
            return {"ok": False, "message": f"No 'result' in response. Keys: {list(r.keys())}", "raw": str(r)[:1000]}
        self.raw_record_b64 = r["result"]
        if r["result"] is None:
            return {"ok": False, "message": "result is None", "raw": str(r)[:1000]}
        dec = decrypt_player_record(r["result"], self.firebase_uid or "", self.password, self.email)
        if dec.get("success"):
            self.record = dec["record"]
            return {"ok": True, "record": self.record}
        return {"ok": False, "message": dec.get("message", "Decrypt failed"), "raw": str(r["result"])[:500]}

    # ── Car / Garage Server Ops ─────────────
    async def get_all_cars(self) -> Dict:
        r = await self._post(EP["get_all_cars"], {"data": None})
        if r:
            self.all_cars = r.get("result", []) if isinstance(r.get("result"), list) else []
        return r or {}

    async def check_garage(self) -> Dict:
        r = await self._post(EP["check_garage"], {"data": None})
        if r:
            self.garage_info = r.get("result", {}) if isinstance(r.get("result"), dict) else {}
        return r or {}

    async def buy_car(self, car_id: int) -> Dict:
        return await self._post(EP["buy_car"], {"data": car_id})

    async def get_car_price(self, car_id: int) -> Dict:
        return await self._post(EP["get_car_price"], {"data": car_id})

    async def save_car(self, car_data: Dict) -> Dict:
        return await self._post(EP["save_car"], {"data": car_data})

    async def exchange_car_for_money(self, car_id: int) -> Dict:
        return await self._post(EP["exchange_car_money"], {"data": car_id})

    async def remove_car_from_db(self, car_id: int) -> Dict:
        return await self._post(EP["remove_car_db"], {"data": car_id})

    # ── Economy ─────────────────────────────
    async def get_money(self) -> Dict:
        return await self._post(EP["get_money"], {"data": None})

    async def get_coins(self) -> Dict:
        return await self._post(EP["get_coins"], {"data": None})

    async def buy_money(self, amount: int) -> Dict:
        return await self._post(EP["buy_money"], {"data": amount})

    async def buy_coins(self, amount: int) -> Dict:
        return await self._post(EP["buy_coins"], {"data": amount})

    # ── Rating ──────────────────────────────
    async def set_rank(self) -> Dict:
        rd = {"RatingData": {"time":1e22,"cars":1e16,"car_fix":1e13,"car_collided":1e12,
            "car_exchange":1e13,"car_trade":1e13,"car_wash":1e13,"slicer_cut":1e13,
            "drift_max":1e14,"drift":1e14,"cargo":1e5,"delivery":1e5,"race_win":3e20,
            "taxi":1e10,"levels":10000990000,"gifts":1e9,"fuel":1e10,"offroad":1e10,
            "speed_banner":1e9,"reactions":1e17,"run":1e9,"real_estate":1e9,
            "t_distance":1e10,"treasure":1e10,"block_post":1e10,"push_ups":1e12,
            "burnt_tire":1e10,"passanger_distance":1e8}}
        return await self._post(EP["set_user_rating"], {"data": json.dumps(rd)})

    async def get_user_rating(self) -> Dict:
        return await self._post(EP["get_user_rating"], {"data": None})

    async def validate_rank(self) -> Dict:
        return await self._post(EP["validate_rank"], {"data": None})

    # ── Events / Misc ───────────────────────
    async def get_all_events(self) -> Dict:
        return await self._post(EP["get_all_events"], {"data": None})

    async def get_offers(self) -> Dict:
        return await self._post(EP["get_offers"], {"data": None})

    async def get_rewards(self) -> Dict:
        return await self._post(EP["get_rewards"], {"data": None})

    async def get_daily_task(self) -> Dict:
        return await self._post(EP["get_daily_task"], {"data": None})

    async def ping(self) -> Dict:
        return await self._post(EP["ping"], {"data": None})

    async def get_user_connection(self) -> Dict:
        return await self._post(EP["get_user_conn"], {"data": None})

    # ── Save Player Record (DANGER) ─────────
    async def save_player_record(self, record: Dict) -> Dict:
        """WARNING: Only use after inspecting the record structure!
        CPM2 may use a different format than CPM1."""
        # This is a placeholder — CPM2 payload format is unknown
        # You would need to implement proper serialization for v23_1
        return {"ok": False, "message": "Not implemented — inspect record first"}


# ═══════════════════════════════════════════
#  🖥️  CLI
# ═══════════════════════════════════════════

def print_banner():
    print(r"""
   ██████╗██████╗ ███╗   ███╗██████╗ 
  ██╔════╝██╔══██╗████╗ ████║██╔══██╗
  ██║     ██████╔╝██╔████╔██║██████╔╝
  ██║     ██╔═══╝ ██║╚██╔╝██║██╔══██╗
  ╚██████╗██║     ██║ ╚═╝ ██║██║  ██║
   ╚═════╝╚═╝     ╚═╝     ╚═╝╚═╝  ╚═╝
      CPM2 Research Tool v1.0
""")

async def interactive():
    print_banner()
    client = CPM2Client()

    email = input("[?] Email: ").strip()
    password = input("[?] Password: ").strip()
    print("[+] Logging in...")
    r = await client.login(email, password)
    if not r.get("ok"):
        print(f"[!] Login failed: {r.get('message')}")
        return
    print(f"[+] Logged in! UID: {client.firebase_uid}")

    # ── STEP 1: INSPECT RECORD ──────────────
    print("\n" + "="*50)
    print("STEP 1: Loading & inspecting player record...")
    print("="*50)
    ld = await client.load_player()
    if ld.get("ok"):
        rec = ld["record"]
        print(f"\n[+] Name: {rec.get('Name')}")
        print(f"[+] Money: {rec.get('money', 0):,}")
        print(f"[+] Coins: {rec.get('coin', 0):,}")
        print(f"[+] Player ID: {rec.get('localID')}")
        print(f"[+] Cars in fcar: {len(rec.get('fcar', []))}")
        print(f"[+] Garage slots (carIDnStatus): {len(rec.get('carIDnStatus', {}).get('carGeneratedIDs', [])) if rec.get('carIDnStatus') else 0}")
        print(f"[+] Wheels: {len(rec.get('wheels', []))}")
        print(f"[+] Animations: {len(rec.get('animations', []))}")
        print(f"[+] Friends: {len(rec.get('FriendsID', []))}")

        # Dump full record to file for analysis
        dump_file = f"cpm2_record_{client.firebase_uid}.json"
        with open(dump_file, "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=2, ensure_ascii=False)
        print(f"\n[+] Full record saved to: {dump_file}")
        print("    >>> OPEN THIS FILE TO SEE THE EXACT STRUCTURE <<<")
    else:
        print(f"[!] Could not load record: {ld.get('message')}")
        raw = ld.get('raw')
        if raw:
            print(f"[!] Raw preview: {raw[:500]}")
        print("    CPM2 may use a different encryption/format than CPM1.")
        print("    Try option [21] to dump raw response.")

    # ── STEP 2: CHECK GARAGE ────────────────
    print("\n" + "="*50)
    print("STEP 2: Checking garage via server...")
    print("="*50)
    g = await client.check_garage()
    print(json.dumps(g, indent=2)[:2000])

    # ── STEP 3: GET ALL CARS ────────────────
    print("\n" + "="*50)
    print("STEP 3: Getting all available cars from server...")
    print("="*50)
    c = await client.get_all_cars()
    cars = client.all_cars
    print(f"[+] Server returned {len(cars)} cars")
    if cars and len(cars) > 0:
        print("\nFirst 10 cars:")
        for i, car in enumerate(cars[:10]):
            print(f"  {i+1}. {json.dumps(car)[:150]}")
        # Save full list
        with open("cpm2_all_cars.json", "w", encoding="utf-8") as f:
            json.dump(cars, f, indent=2, ensure_ascii=False)
        print("\n[+] Full car list saved to: cpm2_all_cars.json")

    # ── MAIN MENU ───────────────────────────
    while True:
        print("\n" + "="*50)
        print("MAIN MENU")
        print("="*50)
        print("  [1]  Inspect Player Record (JSON dump)")
        print("  [2]  Check Garage")
        print("  [3]  Get All Cars")
        print("  [4]  Get Car Price (by ID)")
        print("  [5]  Buy Car (by ID)")
        print("  [6]  Exchange Car for Money")
        print("  [7]  Remove Car from DB")
        print("  [8]  Get Money")
        print("  [9]  Get Coins")
        print("  [10] Buy Money (server)")
        print("  [11] Buy Coins (server)")
        print("  [12] Get User Rating")
        print("  [13] Set Max Rank")
        print("  [14] Validate Rank")
        print("  [15] Get All Events")
        print("  [16] Get Offers")
        print("  [17] Get Daily Task")
        print("  [18] Get Rewards")
        print("  [19] Ping Server")
        print("  [20] Get User Connection Data")
        print("  [21] Dump Last Server Response")
        print("  [0]  Exit")
        print("="*50)
        print("\nNOTE: For car unlock, use Buy Car (option 5) with IDs")
        print("      from the car list. Garage limit = 20 slots.")
        print("="*50)
        choice = input("> ").strip()

        if choice == "0":
            break
        elif choice == "1":
            print(json.dumps(client.record, indent=2)[:3000])
        elif choice == "2":
            r = await client.check_garage()
            print(json.dumps(r, indent=2)[:2000])
        elif choice == "3":
            r = await client.get_all_cars()
            print(f"[+] {len(client.all_cars)} cars")
            for i, car in enumerate(client.all_cars[:20]):
                print(f"  {i+1}. {json.dumps(car)[:120]}")
        elif choice == "4":
            cid = int(input("[?] Car ID: ").strip())
            r = await client.get_car_price(cid)
            print(json.dumps(r, indent=2)[:500])
        elif choice == "5":
            cid = int(input("[?] Car ID to buy: ").strip())
            r = await client.buy_car(cid)
            print(json.dumps(r, indent=2)[:500])
        elif choice == "6":
            cid = int(input("[?] Car ID to exchange: ").strip())
            r = await client.exchange_car_for_money(cid)
            print(json.dumps(r, indent=2)[:500])
        elif choice == "7":
            cid = int(input("[?] Car ID to remove: ").strip())
            r = await client.remove_car_from_db(cid)
            print(json.dumps(r, indent=2)[:500])
        elif choice == "8":
            r = await client.get_money()
            print(json.dumps(r, indent=2)[:500])
        elif choice == "9":
            r = await client.get_coins()
            print(json.dumps(r, indent=2)[:500])
        elif choice == "10":
            amt = int(input("[?] Amount: ").strip())
            r = await client.buy_money(amt)
            print(json.dumps(r, indent=2)[:500])
        elif choice == "11":
            amt = int(input("[?] Amount: ").strip())
            r = await client.buy_coins(amt)
            print(json.dumps(r, indent=2)[:500])
        elif choice == "12":
            r = await client.get_user_rating()
            print(json.dumps(r, indent=2)[:1000])
        elif choice == "13":
            r = await client.set_rank()
            print(json.dumps(r, indent=2)[:500])
        elif choice == "14":
            r = await client.validate_rank()
            print(json.dumps(r, indent=2)[:500])
        elif choice == "15":
            r = await client.get_all_events()
            print(json.dumps(r, indent=2)[:1000])
        elif choice == "16":
            r = await client.get_offers()
            print(json.dumps(r, indent=2)[:1000])
        elif choice == "17":
            r = await client.get_daily_task()
            print(json.dumps(r, indent=2)[:1000])
        elif choice == "18":
            r = await client.get_rewards()
            print(json.dumps(r, indent=2)[:1000])
        elif choice == "19":
            r = await client.ping()
            print(json.dumps(r, indent=2)[:500])
        elif choice == "20":
            r = await client.get_user_connection()
            print(json.dumps(r, indent=2)[:1000])
        elif choice == "21":
            if hasattr(client, '_last_raw_response') and client._last_raw_response:
                with open("cpm2_last_response.json", "w", encoding="utf-8") as f:
                    json.dump(client._last_raw_response, f, indent=2, ensure_ascii=False)
                print("[+] Saved last server response to cpm2_last_response.json")
            elif client.raw_record_b64:
                with open("cpm2_raw_record.b64", "w") as f:
                    f.write(client.raw_record_b64)
                print("[+] Saved to cpm2_raw_record.b64")
            else:
                print("[!] No raw response yet. Run option 1 first.")
        else:
            print("[!] Invalid choice")

    print("[+] Bye!")


if __name__ == "__main__":
    try:
        asyncio.run(interactive())
    except KeyboardInterrupt:
        print("\n[!] Interrupted")
    except Exception as e:
        print(f"[!] Fatal: {e}")
