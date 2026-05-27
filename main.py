# main.py
# 아파트 실거래가 데이터 수집 및 CSV 저장 프로그램 MVP (터미널 실행용)

import os
import re
import csv
import requests
import xml.etree.ElementTree as ET
import configparser
from sigungu_codes import SIGUNGU_CODES

# Path to .env file
ENV_PATH = ".env"

def get_api_key():
    """Reads and parses the API key from .env robustly."""
    if not os.path.exists(ENV_PATH):
        return None
    
    # 1. Try configparser (INI style)
    try:
        config = configparser.ConfigParser()
        config.read(ENV_PATH, encoding="utf-8")
        if "APT" in config and "key" in config["APT"]:
            key = config["APT"]["key"].strip('"\' ')
            if key:
                return key
    except Exception:
        pass
        
    # 2. Try line by line regex parsing (dotenv fallback)
    try:
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                m = re.search(r'^(?:APT_KEY|key)\s*=\s*["\']?([^"\']+)["\']?', line, re.IGNORECASE)
                if m:
                    return m.group(1).strip()
    except Exception:
        pass
        
    return None

API_KEY = get_api_key()

def main():
    print("==================================================")
    print("   아파트 실거래가 수집기 MVP (CSV 내보내기)")
    print("==================================================")
    
    if not API_KEY:
        print("[에러] .env 파일에서 아파트 실거래가 API Key를 찾을 수 없습니다.")
        print("c:\\Users\\knuser\\Documents\\vibecode\\api_practice\\apt\\.env 파일을 확인해 주세요.")
        return
        
    # 1. Sido selection
    print("\n[1] 조회할 시/도를 선택하세요:")
    sido_list = list(SIGUNGU_CODES.keys())
    for idx, sido in enumerate(sido_list):
        print(f" {idx + 1}. {sido}")
        
    try:
        sido_select = int(input("\n번호 선택 (예: 1): ")) - 1
        if sido_select < 0 or sido_select >= len(sido_list):
            raise IndexError()
        selected_sido = sido_list[sido_select]
    except (ValueError, IndexError):
        print("올바르지 않은 입력입니다. '서울특별시'로 기본 설정합니다.")
        selected_sido = "서울특별시"
        
    # 2. Sigungu selection
    sigungu_map = SIGUNGU_CODES[selected_sido]
    sigungu_list = sorted(list(sigungu_map.keys()))
    
    print(f"\n[2] [{selected_sido}]의 시/군/구 목록:")
    # Print in columns for readability
    for idx, sgg in enumerate(sigungu_list):
        print(f" {idx + 1:2d}. {sgg:<12s}", end="\n" if (idx + 1) % 4 == 0 or idx == len(sigungu_list) - 1 else "")
        
    try:
        sgg_select = int(input("\n\n번호 선택 (예: 1): ")) - 1
        if sgg_select < 0 or sgg_select >= len(sigungu_list):
            raise IndexError()
        selected_sgg = sigungu_list[sgg_select]
    except (ValueError, IndexError):
        print("올바르지 않은 입력입니다. 첫 번째 구로 기본 설정합니다.")
        selected_sgg = sigungu_list[0]
        
    sigungu_code = sigungu_map[selected_sgg]
    print(f"\n선택된 행정구역: {selected_sido} {selected_sgg} (법정동코드 앞 5자리: {sigungu_code})")
    
    # 3. Year & Month selection
    year_month = input("계약년월을 입력하세요 (6자리 YYYYMM, 예: 202403): ").strip()
    if not year_month or not re.match(r'^\d{6}$', year_month):
        print("형식이 올바르지 않습니다. '202403'으로 기본 설정합니다.")
        year_month = "202403"
        
    print(f"\n데이터 조회 중... (조회 대상: {selected_sido} {selected_sgg}, 조회년월: {year_month})")
    
    # 4. Call API
    url = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
    params = {
        'serviceKey': API_KEY,
        'LAWD_CD': sigungu_code,
        'DEAL_YMD': year_month,
        'numOfRows': '1000',
        'pageNo': '1'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 403:
            print("\n[오류] API 호출이 거부되었습니다 (403 Forbidden).")
            print("이유: 공공데이터포털에 등록된 서비스키가 활성화 전이거나(승인 후 1-2시간 소요), 권한이 없습니다.")
            return
        elif response.status_code != 200:
            print(f"\n[오류] 공공데이터 API 서버 응답 실패 (HTTP 상태 코드: {response.status_code})")
            return
            
        root = ET.fromstring(response.content)
        
        # Check API status
        header = root.find("header")
        result_code = "00"
        result_msg = "NORMAL SERVICE"
        if header is not None:
            rc = header.find("resultCode")
            rm = header.find("resultMsg")
            if rc is not None: result_code = rc.text.strip()
            if rm is not None: result_msg = rm.text.strip()
            
        if result_code != "00":
            print(f"\n[오류] 공공데이터 API 서버가 에러를 반환했습니다: {result_code} ({result_msg})")
            return
            
        # Parse items
        body = root.find("body")
        items = []
        if body is not None:
            items_node = body.find("items")
            if items_node is not None:
                for item in items_node.findall("item"):
                    item_dict = {}
                    for child in item:
                        item_dict[child.tag] = child.text.strip() if child.text else ""
                    items.append(item_dict)
                    
        if not items:
            print(f"\n[알림] {year_month} 계약 분에 대한 {selected_sido} {selected_sgg} 실거래 내역이 존재하지 않습니다.")
            return
            
        print(f"\n[성공] 총 {len(items)}건의 실거래 데이터를 수집하였습니다!")
        
        # 5. Save to CSV (Excel compatible)
        filename = f"apt_transactions_{selected_sido.replace(' ', '')}_{selected_sgg.replace(' ', '')}_{year_month}.csv"
        
        fields = ["dealYear", "dealMonth", "dealDay", "dong", "aptNm", "area", "floor", "dealAmount", "buildYear", "cancelDealDay"]
        headers_ko = ["계약년", "계약월", "계약일", "법정동", "아파트명", "전용면적(㎡)", "층", "거래금액(만원)", "건축년도", "해제일자"]
        
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(headers_ko)
            for item in items:
                row = [item.get(field, "").replace(",", "") if field == "dealAmount" else item.get(field, "") for field in fields]
                writer.writerow(row)
                
        print(f"💾 엑셀 호환 CSV 파일 저장 완료: {os.path.abspath(filename)}")
        
        # 6. Show Preview
        print("\n--- 📍 상위 5건 실거래 내역 미리보기 ---")
        for idx, item in enumerate(items[:5]):
            price_str = item.get("dealAmount", "").strip().replace(",", "")
            try:
                price_val = int(price_str)
                eok = price_val // 10000
                man = price_val % 10000
                price_formatted = f"{eok}억 {man}만원" if eok > 0 else f"{man}만원"
            except ValueError:
                price_formatted = f"{price_str}만원"
                
            cancel_status = " (거래해제)" if item.get("cancelDealDay") else ""
            print(f" {idx + 1}. {item.get('dealMonth')}/{item.get('dealDay')} | {item.get('dong')} | {item.get('aptNm')} | {item.get('area')}㎡ | {item.get('floor')}층 | {price_formatted}{cancel_status}")
            
    except Exception as e:
        print(f"\n[오류] 프로그램 실행 중 예외가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
