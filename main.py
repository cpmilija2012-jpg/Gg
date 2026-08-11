#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPM Full Unlocker — Termux Edition v2.0
+ Car Unlock via boughtFsos
+ King Rank: SetUserRating 1/2/5/6 (user URLs)
"""

import requests
import json
import struct
import hashlib
import base64
import zlib
import sys
import os
from copy import deepcopy

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

# ═══════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════

FK       = "AIzaSyAe_aOVT1gSfmHKBrorFvX4fRwN5nODXVA"
LOAD_URL = "https://europe-west1-cp-multiplayer.cloudfunctions.net/GetPlayerRecords3"
SAVE_URL = "https://europe-west1-cp-multiplayer.cloudfunctions.net/SavePlayerRecordsPartially8"

# SAMO URL-ovi koje si poslao u prvoj poruci
RANK_URLS = {
    "1": "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating1",
    "2": "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating2",
    "5": "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating5",
    "6": "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating6",
}

MAX_MONEY = 50_000_000
MAX_COIN  = 500_000

GAME_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/json",
    "User-Agent": "UnityPlayer/2022.3.62f2 (UnityWebRequest/1.0, libcurl/8.10.1-DEV)",
    "X-Unity-Version": "2022.3.62f2",
}

# ═══════════════════════════════════════════
#  CRYPTO (identicno kao u main.py)
# ═══════════════════════════════════════════

def make_xor_key(uid: str) -> bytes:
    chars = list(uid)
    if len(chars) >= 9: chars[1], chars[8] = chars[8], chars[1]
    if len(chars) >= 3: chars.pop(2)
    if len(chars) >= 5: chars.append(chars[4])
    return "".join(chars).encode("utf-8")

def xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(data[i] ^ key[i % len(key)] for i in range(len(data)))

def decompress(data: bytes):
    if HAS_BROTLI:
        try: return brotli.decompress(data)
        except: pass
    try: return zlib.decompress(data, zlib.MAX_WBITS | 16)
    except: pass
    try: return zlib.decompress(data)
    except: pass
    return None

def decrypt_aes(data: bytes, key: bytes):
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
#  READER / PARSER
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

# ═══════════════════════════════════════════
#  WRITER / SERIALIZER
# ═══════════════════════════════════════════

class Writer:
    def __init__(self): self._p = []
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
    compressed = brotli.compress(combined) if HAS_BROTLI else zlib.compress(combined)
    encrypted  = xor_bytes(compressed, make_xor_key(uid))
    return base64.b64encode(encrypted).decode("ascii")

# ═══════════════════════════════════════════
#  CPM CLIENT
# ═══════════════════════════════════════════

class CPMTermux:
    def __init__(self):
        self.auth_token = None
        self.refresh_token = None
        self.firebase_uid = ""
        self.email = ""
        self.password = ""
        self.record = None
        self.original = None

    def login(self, email, password):
        self.email = email; self.password = password
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FK}"
        p = {"email":email,"password":password,"returnSecureToken":True,"clientType":"CLIENT_TYPE_ANDROID"}
        h = {"Accept":"*/*","Accept-Encoding":"gzip","Content-Type":"application/json",
             "User-Agent":"UnityPlayer/2022.3.62f2 (UnityWebRequest/1.0, libcurl/8.10.1-DEV)",
             "X-Unity-Version":"2022.3.62f2"}
        try:
            r = requests.post(url, json=p, headers=h, timeout=30)
            data = r.json()
        except Exception as e:
            return {"ok":False,"message":f"NETWORK_ERROR: {e}"}
        if "idToken" in data:
            self.auth_token = data["idToken"]
            self.refresh_token = data.get("refreshToken","")
            self.firebase_uid = data.get("localId","")
            return {"ok":True}
        err = data.get("error",{}).get("message","UNKNOWN")
        return {"ok":False,"message":err}

    def _post(self, url, payload):
        h = {k:v for k,v in {**GAME_HEADERS,"Authorization":f"Bearer {self.auth_token}"}.items() if k.lower()!="host"}
        try:
            r = requests.post(url, json=payload, headers=h, timeout=30)
            try: return r.json()
            except: return {"raw": r.text, "status": r.status_code}
        except Exception as e:
            return {"error": str(e)}

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

    def load(self):
        r = self._post(LOAD_URL, {"data":None})
        if not r or not r.get("result"): return False
        dec = decrypt_player_record(r["result"], self.firebase_uid, self.password, self.email)
        if dec.get("success") and dec.get("record"):
            self.record = dec["record"]
            self.original = deepcopy(self.record)
            return True
        return False

    def save(self):
        if not self.record or not self.firebase_uid:
            return {"ok":False,"message":"Not loaded"}
        payload = build_payload(self.record, self.firebase_uid, self.original)
        r = self._post(SAVE_URL, {"data":{"data":payload,"deviceId":self.firebase_uid[:8]}})
        if r and self._ok(r):
            self.original = deepcopy(self.record)
            return {"ok":True}
        return {"ok":False,"message":f"SAVE_FAILED: {str(r)[:120]}"}

    def _modify(self, mods):
        if not self.record: return {"ok":False,"message":"Load first"}
        for k,v in mods.items():
            if k=="money": v=min(v,MAX_MONEY)
            if k=="coin":  v=min(v,MAX_COIN)
            self.record[k]=v
        return self.save()

    def _set_floats(self, indices_values):
        if not self.record: return {"ok":False,"message":"Load first"}
        fl = self.record.get("floats",[])
        max_idx = max(idx for idx,_ in indices_values)
        while len(fl) <= max_idx: fl.append(0.0)
        for idx,val in indices_values: fl[idx]=float(val)
        self.record["floats"]=fl
        return self.save()

    def _set_integers(self, indices_values):
        if not self.record: return {"ok":False,"message":"Load first"}
        it = self.record.get("integers",[])
        max_idx = max(idx for idx,_ in indices_values)
        while len(it) <= max_idx: it.append(0)
        for idx,val in indices_values: it[idx]=int(val)
        self.record["integers"]=it
        return self.save()

    # ── Core ops ────────────────────────────
    def set_money(self, amount): return self._modify({"money": min(amount, MAX_MONEY)})
    def set_coin(self, amount):  return self._modify({"coin": min(amount, MAX_COIN)})
    def set_name(self, name):    return self._modify({"Name": name})
    def set_id(self, pid):       return self._modify({"localID": pid.upper()})
    def set_wins(self, amount):  return self._set_floats([(8, float(amount))])
    def set_loses(self, amount): return self._set_floats([(9, float(amount))])

    # ── Features ────────────────────────────
    def unlock_w16(self):        return self._set_floats([(32, 1.0)])
    def unlock_horns(self):      return self._set_floats([(27,1.0),(28,1.0),(29,1.0),(30,1.0),(31,1.0)])
    def disable_damage(self):    return self._set_floats([(34, 1.0)])
    def unlimited_fuel(self):    return self._set_floats([(3, 1.0)])
    def unlock_smoke(self):      return self._set_floats([(33, 1.0)])

    def unlock_animations(self):
        if not self.record: return {"ok":False,"message":"Load first"}
        self.record["animations"] = list(set(self.record.get("animations",[]) + list(range(301))))
        return self.save()

    def unlock_wheels(self):
        if not self.record: return {"ok":False,"message":"Load first"}
        self.record["wheels"] = list(set(self.record.get("wheels",[]) + list(range(73,221))))
        it = self.record.get("integers",[])
        while len(it) < 113: it.append(0)
        for i in [0,1,2,3,4,5,110,111,112]: it[i]=1
        self.record["integers"]=it
        return self.save()

    def unlock_houses(self):
        return self._set_integers([(8,1),(110,1),(111,1),(112,1)])

    def complete_levels(self):
        lvl = [0] + [120 if i==43 else 1 for i in range(1,110)]
        return self._modify({"LevelsDoneTime": lvl})

    # ── CARS (boughtFsos) ───────────────────
    def unlock_car(self, car_id):
        """Dodaje jedan auto u boughtFsos"""
        if not self.record: return {"ok":False,"message":"Load first"}
        current = self.record.get("boughtFsos", [])
        if car_id not in current:
            current.append(int(car_id))
            self.record["boughtFsos"] = current
            return self.save()
        return {"ok":True,"message":"Already owned"}

    def unlock_cars_range(self, start, end):
        """Dodaje range ID-jeva u boughtFsos"""
        if not self.record: return {"ok":False,"message":"Load first"}
        current = set(self.record.get("boughtFsos", []))
        new_ids = list(range(int(start), int(end)+1))
        added = [c for c in new_ids if c not in current]
        if added:
            current.update(added)
            self.record["boughtFsos"] = sorted(list(current))
            return self.save()
        return {"ok":True,"message":"All already owned"}

    def unlock_all_cars(self, max_id=250):
        """Dodaje sve auta od 1 do max_id"""
        return self.unlock_cars_range(1, max_id)

    # ── Rank ────────────────────────────────
    def set_rank(self, endpoint="6"):
        url = RANK_URLS.get(endpoint)
        if not url:
            return {"ok":False,"message":f"Unknown endpoint {endpoint}. Use: 1,2,5,6"}
        rd = {"RatingData":{"time":1e22,"cars":1e16,"car_fix":1e13,"car_collided":1e12,
            "car_exchange":1e13,"car_trade":1e13,"car_wash":1e13,"slicer_cut":1e13,
            "drift_max":1e14,"drift":1e14,"cargo":1e5,"delivery":1e5,"race_win":3e20,
            "taxi":1e10,"levels":10000990000,"gifts":1e9,"fuel":1e10,"offroad":1e10,
            "speed_banner":1e9,"reactions":1e17,"run":1e9,"real_estate":1e9,
            "t_distance":1e10,"treasure":1e10,"block_post":1e10,"push_ups":1e12,
            "burnt_tire":1e10,"passanger_distance":1e8}}
        r = self._post(url, {"data":json.dumps(rd)})
        if r and self._ok(r): return {"ok":True}
        return {"ok":False,"message":"RANK_FAILED"}

    def fix_account(self):
        if not self.record: return {"ok":False,"message":"Load first"}
        bugs=0
        fl = (self.record.get("floats",[]))[:54]
        while len(fl)<54: fl.append(0.0)
        fixed_fl=[]
        for v in fl:
            if v in (1,1.0): fixed_fl.append(1.0)
            elif isinstance(v,(int,float)) and v>1: bugs+=1; fixed_fl.append(0.0)
            else: fixed_fl.append(float(v) if v else 0.0)
        it = (self.record.get("integers",[]))[:120]
        while len(it)<120: it.append(0)
        fixed_it=[]
        for v in it:
            if v==1: fixed_it.append(1)
            elif isinstance(v,(int,float)) and v>1: bugs+=1; fixed_it.append(0)
            else: fixed_it.append(int(v) if v else 0)
        self.record["floats"]=fixed_fl; self.record["integers"]=fixed_it
        res = self.save()
        return {"ok":True,"bugs_fixed":bugs} if res.get("ok") else {"ok":False,"message":"FIX_FAILED"}

    def unlock_all(self):
        results = []
        ops = [
            ("W16", self.unlock_w16), ("Horns", self.unlock_horns),
            ("No Damage", self.disable_damage), ("Unlimited Fuel", self.unlimited_fuel),
            ("Smoke", self.unlock_smoke), ("Animations", self.unlock_animations),
            ("Wheels", self.unlock_wheels), ("Houses", self.unlock_houses),
            ("All Levels", self.complete_levels),
        ]
        for name, fn in ops:
            try: r = fn(); results.append((name, r.get("ok",False), r.get("message","")))
            except Exception as e: results.append((name, False, str(e)))
        return results

# ═══════════════════════════════════════════
#  UI
# ═══════════════════════════════════════════

def banner():
    os.system("clear" if os.name!="nt" else "cls")
    print("\n" + "═"*58)
    print("  🔥  CPM FULL UNLOCKER — TERMUX v2.0")
    print("  + Car Unlock  |  King Rank: 1/2/5/6")
    print("═"*58 + "\n")

def show_stats(cpm):
    r = cpm.record
    if not r:
        print("  [!] Nema ucitanih podataka.\n")
        return
    fl = r.get("floats",[])
    wins = int(fl[8]) if len(fl)>8 else 0
    loses = int(fl[9]) if len(fl)>9 else 0
    lvls = r.get("LevelsDoneTime",[])
    done = sum(1 for x in lvls if x and x>0) if lvls else 0
    cars = len(r.get("boughtFsos",[]))
    print(f"  ┌─ ACCOUNT ───────────────────────────┐")
    print(f"  │  👤 {r.get('Name','Unknown')}")
    print(f"  │  🆔 {r.get('localID','—')}")
    print(f"  │  💰 ${r.get('money',0):,}")
    print(f"  │  🪙 {r.get('coin',0):,} coins")
    print(f"  │  🏆 {wins:,}W / {loses:,}L")
    print(f"  │  🎮 {done} levels | 🛞 {len(r.get('wheels',[]))} wheels")
    print(f"  │  🎭 {len(r.get('animations',[]))} anims | 🚗 {cars} cars")
    print(f"  └──────────────────────────────────────┘\n")

def menu():
    print("  [1]  💰  Set Money")
    print("  [2]  🪙  Set Coins")
    print("  [3]  ✏️  Change Name")
    print("  [4]  🆔  Change Player ID")
    print("  [5]  🏆  Set Wins")
    print("  [6]  😞  Set Loses")
    print("  ───────────────────────────────")
    print("  [7]  🚗  Unlock W16")
    print("  [8]  🔊  Unlock Horns")
    print("  [9]  🛡  Disable Damage")
    print("  [10] ⛽ Unlimited Fuel")
    print("  [11] 💨 Unlock Smoke")
    print("  [12] 🎭 Unlock Animations")
    print("  [13] 🛞 Unlock Wheels")
    print("  [14] 🏠 Unlock Houses")
    print("  [15] 🎮 Complete All Levels")
    print("  ───────────────────────────────")
    print("  [16] 🚗  Unlock Specific Car")
    print("  [17] 🚗  Unlock All Cars (1-250)")
    print("  [18] 🚗  Unlock Car Range (custom)")
    print("  ───────────────────────────────")
    print("  [19] 🏅 Set King Rank")
    print("  [20] 🚀 UNLOCK ALL (7-15)")
    print("  [21] 🔧 Fix Account Bugs")
    print("  [22] 🔄 Reload Account")
    print("  [0]  🚪 Exit")
    print("")

def main():
    banner()
    cpm = CPMTermux()

    print("[*] Unesi CPM email:")
    email = input("    >> ").strip()
    print("[*] Unesi password:")
    password = input("    >> ").strip()

    print("\n[+] Login...")
    res = cpm.login(email, password)
    if not res["ok"]:
        print(f"\n[!] LOGIN FAILED: {res['message']}")
        sys.exit(1)
    print(f"[+] Ulogovan! UID: {cpm.firebase_uid}")

    print("\n[+] Ucitavanje accounta...")
    if not cpm.load():
        print("[!] Ne mogu da ucitam account.")
        sys.exit(1)
    print("[+] Account ucitan!\n")

    while True:
        banner()
        show_stats(cpm)
        menu()
        choice = input("  >> ").strip()

        if choice == "0":
            print("\n[+] Dovidjenja."); break

        elif choice == "1":
            try: a = int(input("  Novac (max 50M): ").strip().replace(",",""))
            except: print("  ✗ Greska"); input(); continue
            r = cpm.set_money(a); print(f"  {'✅' if r['ok'] else '❌'} {r.get('message','')}")

        elif choice == "2":
            try: a = int(input("  Kovanice (max 500K): ").strip().replace(",",""))
            except: print("  ✗ Greska"); input(); continue
            r = cpm.set_coin(a); print(f"  {'✅' if r['ok'] else '❌'} {r.get('message','')}")

        elif choice == "3":
            n = input("  Novo ime: ").strip()
            r = cpm.set_name(n); print(f"  {'✅' if r['ok'] else '❌'}")

        elif choice == "4":
            pid = input("  Novi Player ID: ").strip()
            r = cpm.set_id(pid); print(f"  {'✅' if r['ok'] else '❌'}")

        elif choice == "5":
            try: v = int(input("  Wins: ").strip()); assert v>=0
            except: print("  ✗ Greska"); input(); continue
            r = cpm.set_wins(v); print(f"  {'✅' if r['ok'] else '❌'}")

        elif choice == "6":
            try: v = int(input("  Loses: ").strip()); assert v>=0
            except: print("  ✗ Greska"); input(); continue
            r = cpm.set_loses(v); print(f"  {'✅' if r['ok'] else '❌'}")

        elif choice == "7": r = cpm.unlock_w16(); print(f"  {'✅' if r['ok'] else '❌'} W16")
        elif choice == "8": r = cpm.unlock_horns(); print(f"  {'✅' if r['ok'] else '❌'} Horns")
        elif choice == "9": r = cpm.disable_damage(); print(f"  {'✅' if r['ok'] else '❌'} No Damage")
        elif choice == "10": r = cpm.unlimited_fuel(); print(f"  {'✅' if r['ok'] else '❌'} Fuel")
        elif choice == "11": r = cpm.unlock_smoke(); print(f"  {'✅' if r['ok'] else '❌'} Smoke")
        elif choice == "12": r = cpm.unlock_animations(); print(f"  {'✅' if r['ok'] else '❌'} Anims")
        elif choice == "13": r = cpm.unlock_wheels(); print(f"  {'✅' if r['ok'] else '❌'} Wheels")
        elif choice == "14": r = cpm.unlock_houses(); print(f"  {'✅' if r['ok'] else '❌'} Houses")
        elif choice == "15": r = cpm.complete_levels(); print(f"  {'✅' if r['ok'] else '❌'} Levels")

        elif choice == "16":
            try: cid = int(input("  Car ID: ").strip())
            except: print("  ✗ Broj!"); input(); continue
            r = cpm.unlock_car(cid)
            print(f"  {'✅' if r['ok'] else '❌'} {r.get('message','')}")

        elif choice == "17":
            print("  [+] Otkljucavam sve auta (1-250)...")
            r = cpm.unlock_all_cars(250)
            print(f"  {'✅' if r['ok'] else '❌'} {r.get('message','')}")

        elif choice == "18":
            try:
                s = int(input("  Od ID: ").strip())
                e = int(input("  Do ID: ").strip())
            except: print("  ✗ Brojevi!"); input(); continue
            r = cpm.unlock_cars_range(s, e)
            print(f"  {'✅' if r['ok'] else '❌'} {r.get('message','')}")

        elif choice == "19":
            print("  Izaberi King Rank endpoint:")
            print("    [1] SetUserRating1")
            print("    [2] SetUserRating2")
            print("    [5] SetUserRating5")
            print("    [6] SetUserRating6  (preporuceno)")
            ep = input("    >> ").strip()
            r = cpm.set_rank(ep)
            print(f"  {'✅' if r['ok'] else '❌'} Rank ({r.get('message','')})")

        elif choice == "20":
            print("\n  [+] Otkljucavam sve feature...")
            results = cpm.unlock_all()
            for name, ok, msg in results:
                print(f"  {'✅' if ok else '❌'} {name}" + (f" ({msg})" if not ok and msg else ""))
            print("\n  [+] Rank...")
            r = cpm.set_rank("6")
            print(f"  {'✅' if r['ok'] else '❌'} Rank")

        elif choice == "21":
            r = cpm.fix_account()
            print(f"  {'✅' if r['ok'] else '❌'} Fix ({r.get('bugs_fixed',0)} bugs)")

        elif choice == "22":
            print("[+] Reload...")
            if cpm.load(): print("[+] Ucitano!")
            else: print("[!] Greska")

        else:
            print("  ✗ Nepoznata opcija")

        input("\n  [ENTER za nastavak]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Prekinuto.")
        sys.exit(0)
