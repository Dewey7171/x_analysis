import streamlit as st
import requests
import os
from PIL import Image
from io import BytesIO
import time  # time 모듈 추가

# 서버 URL을 환경 변수에서 가져오기
# SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")
SERVER_URL = st.secrets["server"]["SERVER_URL"]

st.title("What do you Keyword a lot?")

username = st.text_input("X Account")

# 리트라이 함수 정의
def retry_request(url, retries=5, delay=3):
    """주어진 URL에 대해 리트라이를 수행하는 함수"""
    for attempt in range(retries):
        response = requests.get(url)
        if response.status_code == 200:
            return response
        else:
            # 실패 시 대기 후 재시도
            time.sleep(delay)  # delay(초)만큼 기다리기
    return None  # 최대 리트라이 횟수를 초과한 경우

if st.button("Start"):
    if username:  # 사용자 아이디가 입력된 경우에만 실행
        # 트윗 크롤링 요청
        response = requests.post(f"{SERVER_URL}/scrape", json={"username": username})
        if response.status_code == 200:
            st.success("Analysis complete")

            # 서버로부터 반환된 파일명은 .json 형식이지만 이미 .png 파일이 생성됨
            filename = response.json().get("file")
            image_name = filename.replace('.json', '.png')

            # 워드클라우드 이미지 경로 가져오기
            wordcloud_response = retry_request(f"{SERVER_URL}/wordcloud/{image_name}", retries=5)

            if wordcloud_response:
                image_file = wordcloud_response.json().get("image_path")
                if image_file:
                    # 이미지 파일을 서버의 'static' 폴더에서 로드
                    image_url = f"{SERVER_URL}/{image_file}"

                    # 이미지를 다운로드
                    image_response = requests.get(image_url)

                    if image_response.status_code == 200:
                        # 이미지 다운로드 및 표시
                        image = Image.open(BytesIO(image_response.content))
                        st.image(image, caption="Hi X", use_container_width=True)
                    else:
                        st.error("Image download failed! Status code: {}".format(image_response.status_code))
                else:
                    st.error("No image file path available.")
            else:
                st.error("Failed to generate wordcloud image. Retry attempts exceeded.")
        else:
            st.error("Failed to scrape tweets.")
    else:
        st.error("Please enter a username.")
