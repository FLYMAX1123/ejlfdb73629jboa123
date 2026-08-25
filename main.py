import os
import json
from datetime import datetime, timedelta

from curl_cffi import requests


THEATER_NAME = "CGV 광교"
THEATER_CODE = "0257"

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
STATE_FILE = "last_dates.json"

BOOKING_PAGE = "https://cgv.co.kr/cnm/movieBook"

API_URL = "https://cgv.co.kr/api/v1/booking/searchMovScnInfo"


def get_open_dates():
    print("CGV 접속 중...")

    session = requests.Session(impersonate="chrome")

    response = session.get(
        BOOKING_PAGE,
        timeout=30
    )

    print("예매 페이지 상태:", response.status_code)

    if response.status_code != 200:
        raise Exception(
            f"CGV 예매 페이지 접속 실패: {response.status_code}"
        )

    open_dates = []

    # 오늘부터 14일 동안 확인
    today = datetime.now()

    for i in range(14):
        target_date = today + timedelta(days=i)
        date_text = target_date.strftime("%Y%m%d")

        try:
            response = session.get(
                API_URL,
                params={
                    "coCd": "A420",
                    "siteNo": THEATER_CODE,
                    "scnYmd": date_text,
                    "rtctlScopCd": "08"
                },
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "ko-KR,ko;q=0.9",
                    "Referer": BOOKING_PAGE
                },
                timeout=30
            )

            print(
                f"{date_text} 상태: {response.status_code}"
            )

            if response.status_code != 200:
                continue

            data = response.json()

            if data.get("statusCode") == 0:
                schedules = data.get("data") or []

                if len(schedules) > 0:
                    open_dates.append(date_text)

                    print(
                        f"🎬 예매 열린 날짜 발견: {date_text}"
                    )

        except Exception as error:
            print(
                f"{date_text} 확인 실패: {error}"
            )

    return sorted(set(open_dates))


def load_previous_dates():
    if not os.path.exists(STATE_FILE):
        return None

    try:
        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        return data.get("dates", [])

    except Exception:
        return None


def save_dates(dates):
    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            {
                "dates": dates
            },
            file,
            ensure_ascii=False,
            indent=2
        )


def send_discord(new_dates):
    if not WEBHOOK_URL:
        print("Discord 웹후크가 없습니다.")
        return

    formatted_dates = []

    for date_text in new_dates:
        date = datetime.strptime(
            date_text,
            "%Y%m%d"
        )

        formatted_dates.append(
            date.strftime("%Y년 %m월 %d일")
        )

    message = (
        f"🎬 **{THEATER_NAME} 신규 예매 오픈!**\n\n"
        "새로운 예매 날짜가 열렸습니다.\n\n"
    )

    for date in formatted_dates:
        message += f"📅 **{date}**\n"

    message += "\n🔔 지금 CGV에서 예매할 수 있습니다!"

    response = requests.post(
        WEBHOOK_URL,
        json={
            "content": message
        },
        timeout=30,
        impersonate="chrome"
    )

    print(
        "Discord 전송 상태:",
        response.status_code
    )


def main():
    print("=" * 40)
    print("CGV 광교 예매 날짜 확인 시작")
    print("=" * 40)

    current_dates = get_open_dates()

    print()
    print("현재 열린 날짜:")
    print(current_dates)

    if not current_dates:
        print("❌ 열린 날짜를 찾지 못했습니다.")
        raise Exception(
            "CGV 데이터를 가져오지 못했습니다."
        )

    previous_dates = load_previous_dates()

    # 처음 실행
    if previous_dates is None:
        print()
        print("첫 실행입니다.")
        print("현재 날짜를 기준값으로 저장합니다.")

        save_dates(current_dates)

        print("기준값 저장 완료!")
        return

    new_dates = sorted(
        set(current_dates) - set(previous_dates)
    )

    if new_dates:
        print()
        print("🔥 새로운 예매 날짜 발견!")
        print(new_dates)

        send_discord(new_dates)

    else:
        print()
        print("새로운 예매 날짜가 없습니다.")

    save_dates(current_dates)


if __name__ == "__main__":
    main()
