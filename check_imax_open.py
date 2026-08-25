import os
import sys
import json
import requests
from datetime import datetime

SITE_NO = "0257"          # 광교 CGV
MOV_NO = "30001323"        # 오디세이 (영화가 바뀌면 이 값만 교체)
CO_CD = "A420"

STATE_FILE = "state.json"
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

API_URL = "https://cgv.co.kr/api/v1/booking/searchSiteScnsCymdListByMov"
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}


def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def send_discord(content):
    if not WEBHOOK_URL:
        log("DISCORD_WEBHOOK_URL이 설정되지 않아 메시지를 보낼 수 없습니다.")
        return
    try:
        requests.post(WEBHOOK_URL, json={"content": content}, timeout=10)
    except Exception as e:
        log(f"디스코드 전송 실패 : {e}")


def get_available_dates():
    response = requests.get(
        API_URL,
        params={"coCd": CO_CD, "siteNo": SITE_NO, "movNo": MOV_NO},
        headers=HEADERS,
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    dates = sorted(item["scnYmd"] for item in data.get("data", []))
    return dates


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)


def format_date(ymd):
    return f"{ymd[0:4]}-{ymd[4:6]}-{ymd[6:8]}"


def main():
    if not WEBHOOK_URL:
        log("오류 : DISCORD_WEBHOOK_URL 환경변수(시크릿)가 없습니다.")
        sys.exit(1)

    try:
        dates = get_available_dates()
    except Exception as e:
        log(f"조회 실패 : {e}")
        sys.exit(1)

    if not dates:
        log("조회된 날짜가 없습니다.")
        return

    current_max_date = dates[-1]
    state = load_state()
    last_max_date = state.get("last_max_date")

    log(f"현재 마지막 예매 가능일 : {current_max_date} (이전 기록 : {last_max_date})")

    if last_max_date is None:
        # 최초 실행 : 알림 없이 기준값만 저장
        log("최초 실행 - 기준값 저장")
        send_discord(f"✅ 광교 IMAX 알리미 연결됨. 현재 마지막 예매 가능일 : **{format_date(current_max_date)}**")
    elif current_max_date > last_max_date:
        log(f"새 날짜 오픈 감지 : {last_max_date} -> {current_max_date}")
        send_discord(
            f"🎬 **광교 CGV IMAX 예매 오픈!**\n"
            f"새로운 날짜 : **{format_date(current_max_date)}**"
        )
    else:
        log("변경 없음")

    save_state({"last_max_date": current_max_date})


if __name__ == "__main__":
    main()
