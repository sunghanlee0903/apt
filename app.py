import os
import re
import requests
import xml.etree.ElementTree as ET
import configparser
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sigungu_codes import SIGUNGU_CODES
from typing import Optional
import random

app = FastAPI(title="Apartment Transaction Price MVP")

# Path to .env file
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")

def get_api_key():
    """Reads and parses the API key from .env robustly."""
    if not os.path.exists(ENV_PATH):
        print("Warning: .env file not found!")
        return None
    
    # 1. Try configparser (INI style)
    try:
        config = configparser.ConfigParser()
        config.read(ENV_PATH, encoding="utf-8")
        if "APT" in config and "key" in config["APT"]:
            key = config["APT"]["key"].strip('"\' ')
            if key:
                return key
    except Exception as e:
        print("Configparser failed, trying line parsing:", e)
        
    # 2. Try line by line regex parsing (dotenv fallback)
    try:
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Match key = "..." or key=... or APT_KEY=...
                m = re.search(r'^(?:APT_KEY|key)\s*=\s*["\']?([^"\']+)["\']?', line, re.IGNORECASE)
                if m:
                    return m.group(1).strip()
    except Exception as e:
        print("Line parsing failed:", e)
        
    return None

def get_kakao_js_key():
    """Reads and parses the Kakao JS key from .env robustly."""
    if not os.path.exists(ENV_PATH):
        return None
    
    # 1. Try configparser (INI style)
    try:
        config = configparser.ConfigParser()
        config.read(ENV_PATH, encoding="utf-8")
        if "kakao" in config and "js_key" in config["kakao"]:
            key = config["kakao"]["js_key"].strip('"\' ')
            if key:
                return key
    except Exception as e:
        print("Configparser failed for kakao, trying line parsing:", e)
        
    # 2. Try line by line regex parsing (dotenv fallback)
    try:
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                m = re.search(r'^(?:js_key|kakao_js_key)\s*=\s*["\']?([^"\']+)["\']?', line, re.IGNORECASE)
                if m:
                    return m.group(1).strip()
    except Exception as e:
        print("Line parsing for kakao key failed:", e)
        
    return None

API_KEY = get_api_key()
print(f"Loaded API Key: {API_KEY[:10]}..." if API_KEY else "No API Key loaded")

KAKAO_JS_KEY = get_kakao_js_key()
print(f"Loaded Kakao JS Key: {KAKAO_JS_KEY[:10]}..." if KAKAO_JS_KEY else "No Kakao JS Key loaded")


# ----------------- Mock Data Generator for high-fidelity Demo Mode -----------------
def generate_mock_transactions(sigungu_code: str, year_month: str):
    """Generates ultra-realistic transaction price data for major districts."""
    random.seed(int(sigungu_code) + int(year_month))
    
    # Find sigungu name
    sido_name = "서울특별시"
    sigungu_name = "강남구"
    found = False
    for sido, sigungus in SIGUNGU_CODES.items():
        for sgg, code in sigungus.items():
            if code == sigungu_code:
                sido_name = sido
                sigungu_name = sgg
                found = True
                break
        if found:
            break
            
    # Year and month parsing
    year = year_month[:4]
    month = year_month[4:]
    
    # Define characteristic apartments per region
    # Format: (Apartment Name, Build Year, Dong, Road Name, Jibun, Base Price in 10,000 Won, Size variations [m2])
    apartments_pool = {
        "11680": [  # Gangnam-gu
            ("압구정 현대 1차 (압구정역)", 1976, "압구정동", "압구정로 29길 10", "369-1", 420000, [131.28, 163.41, 196.21]),
            ("대치 은마 (대치역/학여울역)", 1979, "대치동", "삼성로 212", "316", 240000, [76.79, 84.43]),
            ("개포 디에이치 아너힐즈 (개포동역)", 2019, "개포동", "삼성로 11", "1280", 290000, [59.75, 84.94, 114.95]),
            ("도곡 렉슬 (한티역/도곡역)", 2006, "도곡동", "선릉로 221", "527", 270000, [84.99, 114.99, 134.90]),
            ("역삼 래미안 펜타빌 (역삼역)", 2007, "역삼동", "언주로 311", "709", 230000, [84.97, 115.11]),
            ("삼성 아이파크 (봉은사역/청담역)", 2004, "삼성동", "영동대로 640", "87", 520000, [145.05, 195.38, 226.6])
        ],
        "11440": [  # Mapo-gu
            ("마포 래미안 푸르지오 (애오개역)", 2014, "아현동", "마포대로 195", "801", 175000, [59.96, 84.59, 114.88]),
            ("신촌 그랑자이 (이대역)", 2020, "대흥동", "대흥로 180", "12", 180000, [59.97, 84.98, 112.5]),
            ("마포 프레스티지 자이 (대흥역/공덕역)", 2021, "염리동", "독막로 34길 16", "533", 195000, [59.92, 84.94, 114.97]),
            ("공덕 파크자이 (공덕역)", 2015, "공덕동", "백범로 170", "461", 160000, [84.96, 119.88]),
            ("상암 월드컵파크 7단지 (디지털미디어시티역)", 2005, "상암동", "월드컵북로 434", "1660", 115000, [84.76, 104.28])
        ],
        "41135": [  # Bundang-gu, Seongnam
            ("판교 봇들마을 8단지 (판교역)", 2009, "삼평동", "동판교로 177", "740", 190000, [84.85, 101.45, 115.91]),
            ("서현 시범한양 (서현역)", 1991, "서현동", "분당로 188", "87", 130000, [59.94, 84.90, 134.90]),
            ("정자동 상록우성 (정자역)", 1995, "정자동", "내정로 55", "122", 145000, [69.12, 84.87, 126.96]),
            ("수내동 푸른쌍용 (수내역)", 1992, "수내동", "수내로 118", "66", 135000, [84.90, 101.94, 134.82]),
            ("백현마을 5단지 (판교역)", 2009, "백현동", "판교역로 60", "567", 170000, [74.93, 84.95])
        ]
    }
    
    # Fallback default pool if district is not in the hardcoded ones
    default_pool = [
        ("푸르지오 랜드마크", 2018, "중앙동", "대학로 12", "101-1", 75000, [59.9, 84.9, 114.9]),
        ("아이파크 포레스트", 2015, "힐링동", "숲속마을길 45", "456", 62000, [84.9, 101.5]),
        ("자이 오션뷰", 2021, "해안동", "해안대로 99", "89", 90000, [59.9, 84.9, 135.2]),
        ("래미안 에코그린", 2010, "에코동", "친환경로 2", "12-3", 58000, [84.8, 114.5]),
        ("벽산 타운", 1998, "서부동", "봉화산로 78", "77", 42000, [59.9, 84.9])
    ]
    
    apts = apartments_pool.get(sigungu_code, default_pool)
    transactions = []
    
    # Generate 15 - 35 items
    num_items = random.randint(15, 35)
    for i in range(num_items):
        apt = random.choice(apts)
        name, build_year, dong, road_name, jibun, base_price, sizes = apt
        size = random.choice(sizes)
        
        # Calculate size factor (price increases with size)
        size_factor = size / 84.9
        # Random price fluctuation based on size and some randomness (-10% to +15%)
        random_factor = random.uniform(0.9, 1.15)
        # Apply market variations based on build year (newer = more expensive)
        age_factor = 1.0 + (build_year - 1990) * 0.005 if build_year > 1990 else 0.9
        
        final_price = int(base_price * size_factor * age_factor * random_factor / 1000) * 1000
        # Ensure it's not zero
        if final_price <= 0:
            final_price = base_price
            
        floor = random.randint(1, 28)
        day = str(random.randint(1, 28)).zfill(2)
        
        # Check if canceled (about 3% chance)
        is_canceled = random.random() < 0.03
        cancel_day = f"{year}{month}{str(random.randint(int(day), 28)).zfill(2)}" if is_canceled else ""
        
        transactions.append({
            "aptNm": name,
            "buildYear": str(build_year),
            "dealAmount": f"{final_price:,}",
            "dealYear": year,
            "dealMonth": month,
            "dealDay": day,
            "area": f"{size:.2f}",
            "floor": str(floor),
            "dong": dong,
            "roadname": road_name,
            "jibun": jibun,
            "sigungu": sigungu_name,
            "cancelDealDay": cancel_day,
            "estateAgentSggNm": f"{sigungu_name} 공인중개사"
        })
        
    # Sort by day descending
    transactions.sort(key=lambda x: x["dealDay"], reverse=True)
    return transactions

# ----------------- API Endpoints -----------------

@app.get("/api/sigungu")
def get_sigungu():
    """Returns the Sido/Sigungu list and codes structure."""
    return SIGUNGU_CODES

@app.get("/api/transactions")
def get_transactions(
    sigungu_code: str = Query(..., description="5-digit Sigungu code"),
    year_month: str = Query(..., description="6-digit Year & Month YYYYMM"),
    use_mock: Optional[bool] = Query(None, description="Force demo mock data")
):
    """
    Fetches apartment transactions from Public Data Portal.
    If the API returns 403 Forbidden or fails, it automatically falls back to generating realistic mock data
    and notifies the client through metadata.
    """
    # 1. Force Mock Data if requested or if no API key is available
    api_key = get_api_key()
    if use_mock or not api_key:
        mock_data = generate_mock_transactions(sigungu_code, year_month)
        return {
            "status": "success",
            "source": "demo_mock",
            "message": "Loaded demo high-fidelity transaction data (Mock Mode active)",
            "count": len(mock_data),
            "data": mock_data
        }

    # 2. Query data.go.kr API
    url = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
    params = {
        'serviceKey': api_key,
        'LAWD_CD': sigungu_code,
        'DEAL_YMD': year_month,
        'numOfRows': '500',  # Large enough to get all monthly records
        'pageNo': '1'
    }
    
    try:
        # Use a reasonable timeout (e.g. 6 seconds)
        response = requests.get(url, params=params, timeout=6)
        
        # Check HTTP Status Errors
        if response.status_code == 403:
            print("API returned 403 Forbidden. Falling back to Demo Mode.")
            mock_data = generate_mock_transactions(sigungu_code, year_month)
            return {
                "status": "warning",
                "source": "demo_fallback",
                "message": "Real API returned 403 Forbidden. Switched to high-fidelity Demo Mode.",
                "count": len(mock_data),
                "data": mock_data
            }
        elif response.status_code != 200:
            print(f"API returned status {response.status_code}. Falling back to Demo Mode.")
            mock_data = generate_mock_transactions(sigungu_code, year_month)
            return {
                "status": "warning",
                "source": "demo_fallback",
                "message": f"Real API returned HTTP {response.status_code}. Switched to Demo Mode.",
                "count": len(mock_data),
                "data": mock_data
            }
            
        # Parse XML
        # Note: XML response can sometimes contain error messages in XML format
        try:
            root = ET.fromstring(response.content)
        except Exception as xml_err:
            print("XML Parsing failed, response content was:", response.text[:200])
            mock_data = generate_mock_transactions(sigungu_code, year_month)
            return {
                "status": "warning",
                "source": "demo_fallback",
                "message": "Invalid response format from API. Switched to Demo Mode.",
                "count": len(mock_data),
                "data": mock_data
            }
            
        # Check if the XML is a standard API error header
        header = root.find("header")
        result_code = "00"
        result_msg = "NORMAL SERVICE"
        
        if header is not None:
            rc_node = header.find("resultCode")
            rm_node = header.find("resultMsg")
            if rc_node is not None:
                result_code = rc_node.text.strip()
            if rm_node is not None:
                result_msg = rm_node.text.strip()
                
        # Handle API Errors gracefully
        if result_code != "00":
            print(f"API Error Code {result_code}: {result_msg}. Falling back to Demo Mode.")
            mock_data = generate_mock_transactions(sigungu_code, year_month)
            return {
                "status": "warning",
                "source": "demo_fallback",
                "message": f"API Error {result_code} ({result_msg}). Switched to Demo Mode.",
                "count": len(mock_data),
                "data": mock_data
            }
            
        # Extract items
        body = root.find("body")
        items_list = []
        if body is not None:
            items_node = body.find("items")
            if items_node is not None:
                for item in items_node.findall("item"):
                    item_dict = {}
                    for child in item:
                        tag = child.tag
                        val = child.text.strip() if child.text else ""
                        item_dict[tag] = val
                    items_list.append(item_dict)
                    
        # Return live data if everything is successful
        return {
            "status": "success",
            "source": "live_api",
            "message": "Successfully fetched live transaction data from Public Data Portal.",
            "count": len(items_list),
            "data": items_list
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}. Falling back to Demo Mode.")
        mock_data = generate_mock_transactions(sigungu_code, year_month)
        return {
            "status": "warning",
            "source": "demo_fallback",
            "message": "Failed to connect to the Public Data Portal. Switched to Demo Mode.",
            "count": len(mock_data),
            "data": mock_data
        }

@app.get("/api/kakao-key")
def get_kakao_key():
    """Returns the Kakao Maps JS API Key for the frontend dynamically."""
    js_key = get_kakao_js_key()
    return {"js_key": js_key or ""}

from pydantic import BaseModel

class ClientLog(BaseModel):
    level: str
    message: str
    stack: Optional[str] = None
    url: Optional[str] = None

@app.post("/api/logs")
def post_client_logs(log: ClientLog):
    """Logs client-side errors and warnings to a file for developer analysis."""
    log_path = os.path.join(os.path.dirname(__file__), "client_errors.log")
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{log.level.upper()}] Message: {log.message}\nURL: {log.url}\nStack: {log.stack}\n---\n")
        return {"status": "logged"}
    except Exception as e:
        print("Failed to write client log:", e)
        return {"status": "failed", "error": str(e)}

# Mount static files folder
os.makedirs(os.path.join(os.path.dirname(__file__), "static"), exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    """Serves the static index.html dashboard file."""
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "status": "active",
        "message": "FastAPI Server is running. Static frontend index.html is missing. Please create it in static/index.html"
    }

# Run with uvicorn directly if executed as main script
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
