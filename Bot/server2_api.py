
# The API returned HTML docs page. This is likely because:
# 1. The API provider changed their endpoint structure
# 2. Authentication is wrong
# 3. Need to contact provider for actual API URL
#
# Let me add better error handling and a mock mode for testing

import os
import aiohttp
import asyncio
import json as json_mod
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

# ================= API Configuration =================
API_KEY = os.getenv("TGLION_API_KEY", "i1lfab8cx96eM0jhn3")
YOUR_ID = "233444460"

# Try multiple base URLs
BASE_URLS = [
    "https://api.tg-lion.net",
    "https://tg-lion.net", 
    "https://www.tg-lion.net",
]

_working_base_url = None
_working_method = "GET"

# Mock mode for testing when API is down
MOCK_MODE = os.getenv("SERVER2_MOCK", "false").lower() == "true"

USD_TO_INR_FALLBACK = 85.0
_usd_to_inr_rate = USD_TO_INR_FALLBACK
_last_rate_update = None

_countries_cache = None
_countries_cache_time = None
CACHE_TTL = 30


# ================= Mock Data (for testing) =================
_MOCK_COUNTRIES = {
    "status": "ok",
    "countries": {
        "UZ": {"name": "Uzbekistan 🇺🇿", "code_Num": "40", "code": "UZ", "qty": 6450, "price": "0.80"},
        "UA": {"name": "Ukraine 🇺🇦", "code_Num": "1", "code": "UA", "qty": 425, "price": "1.5"},
        "SA": {"name": "Saudi Arabia 🇸🇦", "code_Num": "53", "code": "SA", "qty": 630, "price": "1.1"},
        "TR": {"name": "Turkey 🇹🇷", "code_Num": "62", "code": "TR", "qty": 1601, "price": "1"},
        "HK": {"name": "Hong Kong 🇭🇰", "code_Num": "14", "code": "HK", "qty": 365, "price": "0.65"},
        "US": {"name": "USA 🇺🇸", "code_Num": "12", "code": "US", "qty": 890, "price": "2.5"},
        "GB": {"name": "UK 🇬🇧", "code_Num": "16", "code": "GB", "qty": 234, "price": "2.0"},
        "IN": {"name": "India 🇮🇳", "code_Num": "22", "code": "IN", "qty": 1200, "price": "0.90"},
        "RU": {"name": "Russia 🇷🇺", "code_Num": "0", "code": "RU", "qty": 3400, "price": "0.75"},
        "DE": {"name": "Germany 🇩🇪", "code_Num": "43", "code": "DE", "qty": 156, "price": "3.0"},
    }
}


async def get_usd_to_inr_rate() -> float:
    global _usd_to_inr_rate, _last_rate_update
    
    if _last_rate_update and (datetime.now(timezone.utc) - _last_rate_update).seconds < 300:
        return _usd_to_inr_rate
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=inr",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    rate = data.get("tether", {}).get("inr", USD_TO_INR_FALLBACK)
                    if rate and rate > 70:
                        _usd_to_inr_rate = float(rate)
                        _last_rate_update = datetime.now(timezone.utc)
                        return _usd_to_inr_rate
    except Exception as e:
        print(f"[Server2] Rate fetch error: {e}")
    
    return _usd_to_inr_rate


def _build_url(base_url: str, action: str, **params) -> str:
    url = f"{base_url}?action={action}&apiKey={API_KEY}&YourID={YOUR_ID}"
    for key, val in params.items():
        if val is not None:
            url += f"&{key}={val}"
    return url


def _build_payload(action: str, **params) -> dict:
    payload = {"action": action, "apiKey": API_KEY, "YourID": YOUR_ID}
    payload.update(params)
    return payload


async def _try_request(action: str, **params) -> Optional[Dict]:
    global _working_base_url, _working_method
    
    if MOCK_MODE:
        print("[Server2] MOCK MODE ACTIVE")
        if action == "available_countries":
            return _MOCK_COUNTRIES
        elif action == "get_balance":
            return {"status": "ok", "balance": "260.5 USD"}
        elif action == "getNumber":
            cc = params.get("country_code", "UZ")
            return {
                "status": "ok",
                "name": _MOCK_COUNTRIES["countries"].get(cc, {}).get("name", cc),
                "Number": "+998901234567",
                "price": _MOCK_COUNTRIES["countries"].get(cc, {}).get("price", "1"),
                "new_balance": 250.0
            }
        elif action == "getCode":
            return {"status": "ok", "Number": params.get("number", ""), "code": "47607", "pass": "2345GD8R"}
        return None
    
    urls_to_try = []
    if _working_base_url:
        urls_to_try.append(_working_base_url)
    for url in BASE_URLS:
        if url not in urls_to_try:
            urls_to_try.append(url)
    
    methods_to_try = [_working_method] if _working_method else []
    if "POST" not in methods_to_try:
        methods_to_try.append("POST")
    if "GET" not in methods_to_try:
        methods_to_try.append("GET")
    
    last_error = None
    
    for base_url in urls_to_try:
        for method in methods_to_try:
            try:
                async with aiohttp.ClientSession() as session:
                    if method == "GET":
                        url = _build_url(base_url, action, **params)
                        async with session.get(url, timeout=15) as resp:
                            text = await resp.text()
                    else:
                        url = base_url
                        payload = _build_payload(action, **params)
                        async with session.post(url, data=payload, timeout=15) as resp:
                            text = await resp.text()
                    
                    print(f"[Server2] {method} {base_url} — Status: {resp.status}")
                    
                    if resp.status != 200:
                        last_error = f"HTTP {resp.status}"
                        continue
                    
                    if text.strip().startswith(("<!DOCTYPE", "<html", "<HTML")):
                        print(f"[Server2] {base_url} returned HTML docs page")
                        last_error = "HTML docs page"
                        continue
                    
                    try:
                        data = json_mod.loads(text)
                        _working_base_url = base_url
                        _working_method = method
                        print(f"[Server2] ✅ Success with {method} {base_url}")
                        return data
                    except json_mod.JSONDecodeError:
                        last_error = f"Invalid JSON: {text[:150]}"
                        continue
                        
            except asyncio.TimeoutError:
                last_error = "Timeout"
                continue
            except Exception as e:
                last_error = str(e)
                continue
    
    print(f"[Server2] ❌ All endpoints failed. Last: {last_error}")
    print("[Server2] 💡 Set SERVER2_MOCK=true in env to use mock data for testing")
    return None


async def api_request(action: str, **params) -> Optional[Dict]:
    return await _try_request(action, **params)


# ================= Public API Methods =================

async def get_available_countries(force_refresh: bool = False) -> Optional[Dict]:
    global _countries_cache, _countries_cache_time
    
    if not force_refresh and _countries_cache and _countries_cache_time:
        if (datetime.now(timezone.utc) - _countries_cache_time).seconds < CACHE_TTL:
            return _countries_cache
    
    data = await api_request("available_countries")
    if data and data.get("status") == "ok":
        _countries_cache = data
        _countries_cache_time = datetime.now(timezone.utc)
        return data
    return None


async def get_country_info(country_code: str) -> Optional[Dict]:
    data = await api_request("country_info", country_code=country_code)
    if data and data.get("status") == "ok":
        return data
    return None


async def get_balance() -> Optional[float]:
    data = await api_request("get_balance")
    if data and data.get("status") == "ok":
        balance_str = data.get("balance", "0 USD").replace("USD", "").strip()
        try:
            return float(balance_str)
        except ValueError:
            return 0.0
    return None


async def buy_number(country_code: str, max_price: Optional[str] = None) -> Optional[Dict]:
    params = {"country_code": country_code}
    if max_price:
        params["maxPrice"] = max_price
    
    data = await api_request("getNumber", **params)
    if data and data.get("status") == "ok":
        return data
    return None


async def get_code(number: str) -> Optional[Dict]:
    data = await api_request("getCode", number=number)
    if data and data.get("status") == "ok":
        return data
    return None


# ================= MongoDB Setup (Added for saving settings) =================
MONGO_URI = os.getenv("MONGO_URI") or "mongodb+srv://brimreading_db_user:Valrikthakur0@cluster0.jxl0eok.mongodb.net/?appName=Cluster0"
try:
    from pymongo import MongoClient
    _db_client = MongoClient(MONGO_URI)
    settings_col = _db_client["tgbitz"]["server2_settings"]
except Exception as e:
    print(f"[Server2] MongoDB connection error: {e}")
    settings_col = None

# ================= Price Conversion & Rounding =================

async def convert_price_to_inr(usd_price, profit_percent: float = 0.0) -> float:
    try:
        usd = float(str(usd_price).replace("USD", "").replace("$", "").strip())
    except (ValueError, TypeError):
        usd = 0.0
    
    rate = await get_usd_to_inr_rate()
    inr_base = usd * rate
    
    if profit_percent > 0:
        inr_final = inr_base * (1 + profit_percent / 100)
    else:
        inr_final = inr_base
    
    # Rounds to nearest 0.5 (e.g. 93.88 -> 94.0, 75.5 -> 75.5, 77.22 -> 77.0)
    return round(inr_final * 2) / 2

def format_price_inr(price: float) -> str:
    if price == int(price):
        return f"₹{int(price)}"
    # Strips unnecessary trailing zeroes and decimals for clean display
    return f"₹{price}".rstrip("0").rstrip(".")

# ================= Admin Price Management =================
_price_settings = {}
_default_profit_percent = 30.0

# Load settings from Database on startup
if settings_col is not None:
    db_settings = settings_col.find_one({"_id": "prices"})
    if db_settings:
        _default_profit_percent = db_settings.get("default_profit", 30.0)
        _price_settings = db_settings.get("countries", {})
    else:
        settings_col.insert_one({"_id": "prices", "default_profit": _default_profit_percent, "countries": _price_settings})

def _save_settings():
    if settings_col is not None:
        settings_col.update_one(
            {"_id": "prices"},
            {"$set": {"default_profit": _default_profit_percent, "countries": _price_settings}},
            upsert=True
        )

def set_profit_percent(percent: float):
    global _default_profit_percent
    _default_profit_percent = percent
    _save_settings()

def get_profit_percent() -> float:
    return _default_profit_percent

def set_country_price(country_code: str, custom_inr: float):
    _price_settings[country_code] = {
        "custom_inr": custom_inr,
        "override": True
    }
    _save_settings()

def set_country_profit(country_code: str, profit_percent: float):
    if country_code not in _price_settings:
        _price_settings[country_code] = {}
    _price_settings[country_code]["profit_percent"] = profit_percent
    _price_settings[country_code]["override"] = False
    _save_settings()

def remove_country_override(country_code: str):
    if country_code in _price_settings:
        del _price_settings[country_code]
        _save_settings()

def get_country_price_settings(country_code: str) -> Dict:
    return _price_settings.get(country_code, {})

async def get_final_price(country_code: str, panel_price_usd) -> Tuple[float, float, float, float]:
    try:
        usd = float(str(panel_price_usd).replace("USD", "").replace("$", "").strip())
    except (ValueError, TypeError):
        usd = 0.0
    
    rate = await get_usd_to_inr_rate()
    inr_base = usd * rate
    
    settings = _price_settings.get(country_code, {})
    
    if settings.get("override") and "custom_inr" in settings:
        final_inr = settings["custom_inr"]
        return usd, inr_base, 0.0, round(final_inr * 2) / 2
    
    if "profit_percent" in settings:
        profit = settings["profit_percent"]
    else:
        profit = _default_profit_percent
    
    final = inr_base * (1 + profit / 100)
    final_rounded = round(final * 2) / 2
    return usd, inr_base, profit, final_rounded

def get_all_price_settings() -> Dict:
    return dict(_price_settings)

def bulk_update_profit(percent: float):
    global _default_profit_percent, _price_settings
    _default_profit_percent = percent
    to_remove = [k for k, v in _price_settings.items() if not v.get("override")]
    for k in to_remove:
        del _price_settings[k]
    _save_settings()
    
