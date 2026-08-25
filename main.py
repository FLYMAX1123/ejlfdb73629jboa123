import os
import json
import requests
from datetime import datetime, timedelta

THEATER_NAME = "CGV 광교"
THEATER_CODE = "0257"

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

STATE_FILE = "last_dates.json"

API_URL = (
    "https://m.cgv.co.kr/WebAPP/Reservation/Common/"
    "ajaxTheaterScheduleList.aspx/GetTheaterScheduleList"
)


def get_open_dates():
    """CGV 광교에서 현재 상영 일정이 열린 날짜를 찾습니다."""

    open_dates = []

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://m.cgv.co.kr",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
        ),
    }

    today = datetime.now()

    # 오늘부터 앞으로 30일을 확인
    for i in range(30):
        target_date = today + timedelta(days=i)
        date_text = target_date.strftime("%Y%m%d")

        payload = {
            "strRequestType": "THEATER",
            "strUserID": "",
            "strMovieGroupCd": "",
            "strMovieTypeCd": "",
            "strPlayYMD": date_text,
            "strTheaterCd": THEATER_CODE,
            "strScreenTypeCd": "",
            "strRankType": "MOVIE",
        }

        try:
            response = requests.post(
                API_URL,
                json=payload,
                headers=headers,
                timeout=10,
            )

            response.raise_for_status()

            outer_data = response.json()
            data = json.loads(outer_data["d"])

            if data.get("ResultCode") == "00000":
                schedules = data.get("ResultSchedule", {}).get(
                    "ScheduleList", []
                )

                if schedules:
                    open_dates.append(date_text)

                    print(
                        f"예매 열린 날짜 발견: {date_text}"
                    )

        except Exception as error:
            print(
                f"{date_text} 확인 실패: {error}"
            )

    return sorted(set(open_dates))


def load_previous_dates():
    """이전에 확인한 날짜를 불러옵니다."""

    if not os.path.exists(STATE_FILE):
        return None

    try:
        with open(
            STATE_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        return data.get("dates", [])

    except Exception:
        return None


def save_dates(dates):
    """현재 날짜 목록을 저장합니다."""

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            {"dates": dates},
            file,
            ensure_ascii=False,
            indent=2,
        )


def send_discord(new_dates):
    """새로운 날짜가 발견되면 Discord에 알립니다."""

    if not WEBHOOK_URL:
        print(
            "DISCORD_WEBHOOK_URL이 없습니다."
        )
        return

    formatted_dates = []

    for date_text in new_dates:
        date_object = datetime.strptime(
            date_text,
            "%Y%m%d",
        )

        formatted_dates.append(
            date_object.strftime("%Y년 %m월 %d일")
        )

    date_list = "\n".join(
        f"📅 **{date}**"
        for date in formatted_dates
    )

    message = {
        "content": (
            "🎬 **CGV 광교 신규 예매 오픈!**\n\n"
            "새로운 예매 날짜가 열렸습니다.\n\n"
            f"{date_list}\n\n"
            "🔔 CGV 광교 예매 페이지를 확인하세요!"
        )
    }

    response = requests.post(
        WEBHOOK_URL,
        json=message,
        timeout=10,
    )

    if response.status_code in [200, 204]:
        print(
            "Discord 알림 전송 성공!"
        )
    else:
        print(
            "Discord 알림 전송 실패:"
        )
        print(response.status_code)
        print(response.text)


def main():
    print("=" * 40)
    print("CGV 광교 예매 날짜 확인 시작")
    print("=" * 40)

    current_dates = get_open_dates()

    print()
    print(
        "현재 열린 날짜:",
        current_dates,
    )

    if not current_dates:
        print(
            "열린 날짜를 찾지 못했습니다."
        )
        print(
            "데이터를 저장하지 않습니다."
        )
        return

    previous_dates = load_previous_dates()

    # 처음 실행하는 경우
    if previous_dates is None:
        print()
        print(
            "첫 실행입니다."
        )
        print(
            "현재 날짜를 기준값으로 저장합니다."
        )

        save_dates(current_dates)

        print(
            "기준값 저장 완료!"
        )

        return

    # 새로 추가된 날짜 찾기
    new_dates = sorted(
        set(current_dates)
        - set(previous_dates)
    )

    if new_dates:
        print()
        print(
            "새로운 예매 날짜 발견!"
        )
        print(new_dates)

        send_discord(new_dates)

    else:
        print()
        print(
            "새로운 예매 날짜가 없습니다."
        )

    # 현재 상태 저장
    save_dates(current_dates)


if __name__ == "__main__":
    main()
