#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPM2 Server Interaction Tool
============================
Built from leaked CPM2 cloud function endpoints.
Supports: Firebase auth, player record R/W, car/coin/money ops, rating, etc.

Usage:
    python cpm2_tool.py
"""

import asyncio
import aiohttp
import base64
import brotli
import hashlib
import json
import re
import struct
import sys
import time
import zlib
from copy import deepcopy
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    print("[!] pip install pycryptodome for AES support")

# ═══════════════════════════════════════════
#  ⚙️  CONFIG
# ═══════════════════════════════════════════

API_KEY = "AIzaSyCQDz9rgjgmvmFkvVfmvr2-7fT4tfrzRRQ"
BASE_URL = "https://europe-west1-cpm-2-7cea1.cloudfunctions.net"

# ═══════════════════════════════════════════
#  🌐 ENDPOINTS
# ═══════════════════════════════════════════

ENDPOINTS = {
    # Auth / Account
    "can_sign_in_anon":    f"{BASE_URL}/CanSignInAnon22_1",
    "can_sign_up":         f"{BASE_URL}/CanSignUp22_1",
    "change_email_pass":   f"{BASE_URL}/ChangeEmailAndPassword23_1",
    "delete_account":      f"{BASE_URL}/DeleteAccount23_1",
    "migrate_anon":        f"{BASE_URL}/MigrateAnonymous23_1",
    "fix_local_id_email":  f"{BASE_URL}/FixLocalIdAndEmail23_1",
    "is_email_in_use":     f"{BASE_URL}/IsEmailInUse23_1",
    "check_local_id":      f"{BASE_URL}/CheckLocalIDUniqueOrGenerateNew22_1",
    "save_app_version":    f"{BASE_URL}/SaveAppVersionOnAccountCreated22_1",
    "get_user_conn":       f"{BASE_URL}/GetUserConnectionData23_1",
    "get_user_conn_22":    f"{BASE_URL}/GetUserConnectionData22_1",

    # Player Data
    "get_player_records":  f"{BASE_URL}/GetPlayerRecords23_1",
    "save_player_records": f"{BASE_URL}/SavePlayerRecords23_1",
    "get_money":           f"{BASE_URL}/GetMoney23_1",
    "get_coins":           f"{BASE_URL}/GetCoins23_1",
    "buy_money":           f"{BASE_URL}/BuyMoney21_1",
    "buy_coins":           f"{BASE_URL}/BuyCoins21_1",
    "spend_coins":         f"{BASE_URL}/SpendCoins23_1",
    "save_wallet":         f"{BASE_URL}/SaveWalletData23_1",

    # Cars
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

    # Inventory / Parts
    "save_engine_inv":     f"{BASE_URL}/SaveEngineInventory23_1",
    "save_parts_inv":      f"{BASE_URL}/SavePartsInventory23_1",
    "save_slots":          f"{BASE_URL}/SaveSlotsCollection23_1",
    "save_plate_vinyls":   f"{BASE_URL}/SavePlateVinyls23_1",

    # Social / Friends
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
}

GAME_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/json",
    "User-Agent": "UnityPlayer/2022.3.62f2 (UnityWebRequest/1.0, libcurl/8.10.1-DEV)",
    "X-Unity-Version": "2022.3.62f2",
}

# ═══════════════════════════════════════════
#  🔐 CRYPTO
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
#  📖 READER / WRITER
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
            "hair": self.read_list(self.read_int),
            "face": self.read_list(self.read_int),
            "beard": self.read_list(self.read_int),
            "cap": self.read_list(self.read_int),
            "mask": self.read_list(self.read_int),
            "top": self.read_list(self.read_int),
            "gloves": self.read_list(self.read_int),
            "bag": self.read_list(self.read_int),
            "pants": self.read_list(self.read_int),
            "shoes": self.read_list(self.read_int),
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
            d  = decompress(xp)
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


class Writer:
    def __init__(self): self._p: List[bytes] = []
    def write_byte(self, v): self._p.append(bytes([v & 0xFF]))
    def write_int(self, v):  self._p.append(struct.pack("<i", int(v or 0)))
    def write_float(self, v): self._p.append(struct.pack("<f", float(v or 0.0)))

    def write_string(self, s):
        if s is None: self._p.append(struct.pack("<i", -1)); return
        s = str(s)
        if s == "": self._p.append(struct.pack("<i", 0)); return
        enc = s.encode("utf-8")
        self._p.append(struct.pack("<ii", -(len(enc)) - 1, len(s)) + enc)

    def write_list(self, lst, fn):
        if lst is None: self._p.append(struct.pack("<i", -1)); return
        self._p.append(struct.pack("<i", len(lst)))
        for item in lst: fn(item)

    def write_equipment(self, data):
        if not data: self.write_byte(0); return
        self.write_byte(13)
        for k in ["hair","face","beard","cap","mask","top","gloves","bag","pants","shoes","glasses","SelectedEquipments"]:
            self.write_list(data.get(k, []), self.write_int)
        self.write_int(data.get("Gender", 0))

    def write_plates(self, data):
        if not data: self.write_byte(0); return
        self.write_byte(1)
        plates = data.get("allPlates", [])
        self._p.append(struct.pack("<i", len(plates)))
        for plate in plates:
            self.write_byte(4)
            self.write_int(plate.get("plateId", 0))
            self.write_int(plate.get("frontCarId", 0))
            self.write_int(plate.get("rearCarId", 0))
            vinyls = plate.get("vinyls", [])
            self._p.append(struct.pack("<i", len(vinyls)))
            for vinyl in vinyls:
                self.write_byte(4)
                vecs = vinyl.get("vectors", [])
                self._p.append(struct.pack("<i", len(vecs)))
                for vec in vecs:
                    self._p.append(struct.pack("<fff", vec.get("x",0), vec.get("y",0), vec.get("z",0)))
                self.write_list(vinyl.get("v", []), self.write_string)
                self.write_list(vinyl.get("floats", []), self.write_float)
                self.write_string(vinyl.get("text", ""))

    def write_car_id_status(self, data):
        if not data: self.write_byte(0); return
        self.write_byte(2)
        self.write_list(data.get("carGeneratedIDs", []), self.write_string)
        self.write_list(data.get("carStatus", []), self.write_int)

    def to_bytes(self): return b"".join(self._p)


FIELD_MAPPING = [
    (1,"localID"),(2,"money"),(3,"Name"),(4,"coin"),(5,"allData"),
    (6,"boughtFsos"),(7,"boughtPoliceLights"),(8,"boughtPoliceSirens"),
    (9,"FriendsID"),(10,"LevelsDoneTime"),(11,"floats"),(12,"integers"),
    (13,"fcar"),(14,"favouriteWheels"),(15,"favouriteVinyls"),
    (16,"favouriteEmojis"),(18,"emojiPacks"),
    (41,"personEquipmentsMale"),(42,"personEquipmentsFemale"),
    (43,"platesData"),(44,"carIDnStatus"),(45,"flags"),
    (46,"animations"),(48,"wheels"),
]

INT_LIST_FIELDS   = {6,7,8,12,13,14,15,16,18,46,48}
FLOAT_LIST_FIELDS = {10,11}
ALWAYS_SEND       = {"allData"}


def _field_modified(nv, ov):
    if nv is None and ov is None: return False
    if nv is None or ov is None: return True
    if type(nv) != type(ov): return True
    if isinstance(nv, (dict,list)):
        return json.dumps(nv,sort_keys=True) != json.dumps(ov,sort_keys=True)
    return nv != ov


def serialize_field(fid, value):
    w = Writer()
    if fid in (1,3,5): w.write_string(value); return w.to_bytes()
    if fid in (2,4): w.write_int(value or 0); return w.to_bytes()
    if fid == 9:
        friends = value or []
        w._p.append(struct.pack("<i", len(friends)))
        for f in friends:
            w.write_byte(3)
            w.write_string((f or {}).get("id",""))
            w.write_string((f or {}).get("Name",""))
            w.write_string((f or {}).get("accountID",""))
        return w.to_bytes()
    if fid in INT_LIST_FIELDS: w.write_list(value or [], w.write_int); return w.to_bytes()
    if fid in FLOAT_LIST_FIELDS: w.write_list(value or [], w.write_float); return w.to_bytes()
    if fid in (41,42): w.write_equipment(value); return w.to_bytes()
    if fid == 43: w.write_plates(value); return w.to_bytes()
    if fid == 44: w.write_car_id_status(value); return w.to_bytes()
    if fid == 45:
        flags = value or {}
        w._p.append(struct.pack("<i", len(flags)))
        for k, v in flags.items():
            w.write_int(int(k)); w.write_int(int(v))
        return w.to_bytes()
    return None


def build_payload(record, uid, original=None):
    fields = []
    for fid, key in FIELD_MAPPING:
        value = record.get(key)
        if value is None: continue
        if key in ALWAYS_SEND:
            should = isinstance(value, str) and len(value) > 0
        elif original is not None:
            should = _field_modified(value, original.get(key))
        else:
            should = True
        if not should: continue
        raw = serialize_field(fid, value)
        if raw is not None: fields.append((fid, raw))

    parts = [struct.pack("<i", len(fields))]
    for fid, raw in fields:
        parts.append(struct.pack("<hi", fid, len(raw)))
        parts.append(raw)
    combined   = b"".join(parts)
    compressed = brotli.compress(combined)
    encrypted  = xor_bytes(compressed, make_xor_key(uid))
    return base64.b64encode(encrypted).decode("ascii")


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
        self.original_record: Dict[str, Any] = {}

    # ── HTTP ────────────────────────────────
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

    # ── Auth ────────────────────────────────
    async def login(self, email: str, password: str) -> Dict:
        self.email = email
        self.password = password
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
        p = {"email": email, "password": password, "returnSecureToken": True, "clientType": "CLIENT_TYPE_ANDROID"}
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout, connector=aiohttp.TCPConnector(ssl=False)) as s:
                async with s.post(url, json=p, headers=GAME_HEADERS) as resp:
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
        url = f"https://securetoken.googleapis.com/v1/token?key={API_KEY}"
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout, connector=aiohttp.TCPConnector(ssl=False)) as s:
                async with s.post(url, json={"grant_type":"refresh_token","refresh_token":self.refresh_token},
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
        r = await self._post(ENDPOINTS["get_player_records"], {"data": None})
        if not r or not r.get("result"):
            return {"ok": False, "message": "No result"}
        dec = decrypt_player_record(r["result"], self.firebase_uid or "", self.password, self.email)
        if dec.get("success"):
            self.original_record = deepcopy(dec["record"])
            self.record = dec["record"]
            return {"ok": True, "record": self.record}
        return {"ok": False, "message": dec.get("message", "Decrypt failed")}

    async def save_player(self, data: Optional[Dict] = None) -> Dict:
        if data is None: data = self.record
        if not self.firebase_uid:
            return {"ok": False, "message": "No UID"}
        payload = build_payload(data, self.firebase_uid, self.original_record)
        r = await self._post(ENDPOINTS["save_player_records"],
                             {"data": {"data": payload, "deviceId": self.firebase_uid[:8]}})
        if r and r.get("result") in (1, True, "1"):
            self.original_record = deepcopy(data)
            return {"ok": True}
        return {"ok": False, "message": str(r)[:200]}

    # ── Modifiers ───────────────────────────
    async def set_money(self, amount: int) -> Dict:
        self.record["money"] = min(amount, 50_000_000)
        return await self.save_player()

    async def set_coin(self, amount: int) -> Dict:
        self.record["coin"] = min(amount, 500_000)
        return await self.save_player()

    async def set_name(self, name: str) -> Dict:
        self.record["Name"] = name
        return await self.save_player()

    async def set_player_id(self, pid: str) -> Dict:
        self.record["localID"] = pid.upper()
        return await self.save_player()

    async def unlock_all_cars(self) -> Dict:
        self.record["fcar"] = list(set(self.record.get("fcar", []) + list(range(1, 250))))
        return await self.save_player()

    async def unlock_wheels(self) -> Dict:
        self.record["wheels"] = list(set(self.record.get("wheels", []) + list(range(73, 221))))
        it = self.record.get("integers", [])
        while len(it) < 113: it.append(0)
        for i in [0,1,2,3,4,5,110,111,112]: it[i] = 1
        self.record["integers"] = it
        return await self.save_player()

    async def unlock_animations(self) -> Dict:
        self.record["animations"] = list(set(self.record.get("animations", []) + list(range(301))))
        return await self.save_player()

    async def complete_levels(self) -> Dict:
        self.record["LevelsDoneTime"] = [0] + [120 if i == 43 else 1 for i in range(1, 110)]
        return await self.save_player()

    async def set_rank(self) -> Dict:
        rd = {"RatingData": {"time":1e22,"cars":1e16,"car_fix":1e13,"car_collided":1e12,
            "car_exchange":1e13,"car_trade":1e13,"car_wash":1e13,"slicer_cut":1e13,
            "drift_max":1e14,"drift":1e14,"cargo":1e5,"delivery":1e5,"race_win":3e20,
            "taxi":1e10,"levels":10000990000,"gifts":1e9,"fuel":1e10,"offroad":1e10,
            "speed_banner":1e9,"reactions":1e17,"run":1e9,"real_estate":1e9,
            "t_distance":1e10,"treasure":1e10,"block_post":1e10,"push_ups":1e12,
            "burnt_tire":1e10,"passanger_distance":1e8}}
        r = await self._post(ENDPOINTS["set_user_rating"], {"data": json.dumps(rd)})
        if r and r.get("result") in (1, True, "1"):
            return {"ok": True}
        return {"ok": False, "message": "RANK_FAILED"}

    # ── Economy ─────────────────────────────
    async def get_money(self) -> Dict:
        return await self._post(ENDPOINTS["get_money"], {"data": None})

    async def get_coins(self) -> Dict:
        return await self._post(ENDPOINTS["get_coins"], {"data": None})

    async def buy_money(self, amount: int) -> Dict:
        return await self._post(ENDPOINTS["buy_money"], {"data": amount})

    async def buy_coins(self, amount: int) -> Dict:
        return await self._post(ENDPOINTS["buy_coins"], {"data": amount})

    # ── Cars ────────────────────────────────
    async def get_all_cars(self) -> Dict:
        return await self._post(ENDPOINTS["get_all_cars"], {"data": None})

    async def buy_car(self, car_id: int) -> Dict:
        return await self._post(ENDPOINTS["buy_car"], {"data": car_id})

    async def save_car(self, car_data: Dict) -> Dict:
        return await self._post(ENDPOINTS["save_car"], {"data": car_data})

    async def check_garage(self) -> Dict:
        return await self._post(ENDPOINTS["check_garage"], {"data": None})

    # ── Misc ────────────────────────────────
    async def ping(self) -> Dict:
        return await self._post(ENDPOINTS["ping"], {"data": None})

    async def get_rewards(self) -> Dict:
        return await self._post(ENDPOINTS["get_rewards"], {"data": None})

    async def get_offers(self) -> Dict:
        return await self._post(ENDPOINTS["get_offers"], {"data": None})

    async def get_all_events(self) -> Dict:
        return await self._post(ENDPOINTS["get_all_events"], {"data": None})

    async def get_user_rating(self) -> Dict:
        return await self._post(ENDPOINTS["get_user_rating"], {"data": None})

    async def validate_rank(self) -> Dict:
        return await self._post(ENDPOINTS["validate_rank"], {"data": None})

    async def get_daily_task(self) -> Dict:
        return await self._post(ENDPOINTS["get_daily_task"], {"data": None})

    async def get_user_connection(self) -> Dict:
        return await self._post(ENDPOINTS["get_user_conn"], {"data": None})

    # ── Batch unlock ────────────────────────
    async def unlock_all(self):
        ops = [
            ("Money", lambda: self.set_money(50_000_000)),
            ("Coins", lambda: self.set_coin(500_000)),
            ("Cars", self.unlock_all_cars),
            ("Wheels", self.unlock_wheels),
            ("Animations", self.unlock_animations),
            ("Levels", self.complete_levels),
            ("Rank", self.set_rank),
        ]
        results = []
        for name, fn in ops:
            try:
                r = await fn()
                results.append((name, r.get("ok", False)))
            except Exception as e:
                results.append((name, False))
            await asyncio.sleep(0.3)
        return results


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
         CPM2 Server Tool v1.0
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

    print("[+] Loading player data...")
    ld = await client.load_player()
    if ld.get("ok"):
        rec = ld["record"]
        print(f"[+] Name: {rec.get('Name')}")
        print(f"[+] Money: {rec.get('money', 0):,}")
        print(f"[+] Coins: {rec.get('coin', 0):,}")
        print(f"[+] Cars: {len(rec.get('fcar', []))}")
    else:
        print(f"[!] Could not load: {ld.get('message')}")

    while True:
        print("\n" + "="*40)
        print("  [1] Set Money ($50M)")
        print("  [2] Set Coins (500K)")
        print("  [3] Unlock All Cars")
        print("  [4] Unlock Wheels")
        print("  [5] Unlock Animations")
        print("  [6] Complete All Levels")
        print("  [7] Set Max Rank")
        print("  [8] ★ UNLOCK ALL ★")
        print("  [9] Change Name")
        print("  [10] Change Player ID")
        print("  [11] Get All Cars (server)")
        print("  [12] Get Offers")
        print("  [13] Get Events")
        print("  [14] Get User Rating")
        print("  [15] Validate Rank")
        print("  [16] Get Daily Task")
        print("  [17] Ping Server")
        print("  [18] Save Current Record")
        print("  [0] Exit")
        print("="*40)
        choice = input("> ").strip()

        if choice == "0":
            break
        elif choice == "1":
            r = await client.set_money(50_000_000)
            print("[+] OK" if r.get("ok") else f"[!] {r.get('message')}")
        elif choice == "2":
            r = await client.set_coin(500_000)
            print("[+] OK" if r.get("ok") else f"[!] {r.get('message')}")
        elif choice == "3":
            r = await client.unlock_all_cars()
            print("[+] OK" if r.get("ok") else f"[!] {r.get('message')}")
        elif choice == "4":
            r = await client.unlock_wheels()
            print("[+] OK" if r.get("ok") else f"[!] {r.get('message')}")
        elif choice == "5":
            r = await client.unlock_animations()
            print("[+] OK" if r.get("ok") else f"[!] {r.get('message')}")
        elif choice == "6":
            r = await client.complete_levels()
            print("[+] OK" if r.get("ok") else f"[!] {r.get('message')}")
        elif choice == "7":
            r = await client.set_rank()
            print("[+] OK" if r.get("ok") else f"[!] {r.get('message')}")
        elif choice == "8":
            print("[+] Running batch unlock...")
            results = await client.unlock_all()
            for name, ok in results:
                print(f"  {'✓' if ok else '✗'} {name}")
        elif choice == "9":
            name = input("[?] New name: ").strip()
            r = await client.set_name(name)
            print("[+] OK" if r.get("ok") else f"[!] {r.get('message')}")
        elif choice == "10":
            pid = input("[?] New Player ID: ").strip()
            r = await client.set_player_id(pid)
            print("[+] OK" if r.get("ok") else f"[!] {r.get('message')}")
        elif choice == "11":
            r = await client.get_all_cars()
            print(json.dumps(r, indent=2)[:1000])
        elif choice == "12":
            r = await client.get_offers()
            print(json.dumps(r, indent=2)[:1000])
        elif choice == "13":
            r = await client.get_all_events()
            print(json.dumps(r, indent=2)[:1000])
        elif choice == "14":
            r = await client.get_user_rating()
            print(json.dumps(r, indent=2)[:1000])
        elif choice == "15":
            r = await client.validate_rank()
            print(json.dumps(r, indent=2)[:1000])
        elif choice == "16":
            r = await client.get_daily_task()
            print(json.dumps(r, indent=2)[:1000])
        elif choice == "17":
            r = await client.ping()
            print(json.dumps(r, indent=2)[:500])
        elif choice == "18":
            r = await client.save_player()
            print("[+] OK" if r.get("ok") else f"[!] {r.get('message')}")
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
