import os
import json
import requests
from datetime import datetime

THEATER_NAME = "CGV 광교"
THEATER_CODE = "0257"

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

if not WEBHOOK_URL:
    raise Exception("DISCORD_WEBHOOK_URL이 설정되지 않았습니다.")

message = {
    "content": f"🎬 **{THEATER_NAME} 알리미 테스트**\n\n"
               f"극장 코드: `{THEATER_CODE}`\n"
               f"현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
               f"웹후크 연결이 정상적으로 작동합니다! ✅"
}

response = requests.post(
    WEBHOOK_URL,
    json=message,
    timeout=10
)

if response.status_code in [200, 204]:
    print("Discord 알림 전송 성공!")
else:
    print("Discord 알림 전송 실패")
    print(response.status_code)
    print(response.text)
