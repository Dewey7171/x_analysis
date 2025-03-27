from wordcloud import WordCloud
import numpy as np
from PIL import Image
import json
import os
import logging
from pathlib import Path

# 로그 설정
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 워드클라우드 이미지 저장 폴더
STATIC_DIR = Path(__file__).resolve().parent / "static"
# 로고 마스크 파일 경로
LOGO_PATH = STATIC_DIR / "logo_mask.png"
FONT_PATH = "./static/font/Pretendard-SemiBold.otf"

def generate_wordcloud(filename):
    """워드클라우드 이미지를 생성하고 저장하는 함수"""
    try:
        # JSON 파일 열기
        logger.info(f"파일 {filename}을 열고 있습니다.")
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 단어 빈도 가져오기
        word_counts = data.get("words", {})
        if not word_counts:
            raise ValueError("단어 빈도 데이터가 없습니다.")

        logger.info("단어 빈도 데이터 로드 완료.")

        # 로고 마스크 로드 (마스크 이미지가 존재할 경우 적용)
        mask = None
        if LOGO_PATH.exists():
            logger.info(f"로고 마스크 {LOGO_PATH}을 불러오고 있습니다.")
            mask = np.array(Image.open(LOGO_PATH).convert("L"))  # 흑백 변환
            mask = np.where(mask > 128, 255, 0)  # 마스크 처리 (배경: 흰색, 로고: 검은색)
        else:
            logger.warning("로고 마스크 파일이 존재하지 않아 기본형 워드클라우드를 생성합니다.")

        # 워드클라우드 생성
        logger.info("워드클라우드를 생성하고 있습니다.")
        wordcloud = WordCloud(
            font_path=FONT_PATH,
            width=800, height=400,
            background_color="#121212",  # 검은색 배경
            mask=mask,  # 로고 마스크 적용 (없으면 기본형)
            contour_width=0,  # 테두리 두께
            contour_color="white",
            colormap="plasma"  # 테두리 색상 (흰색)
        ).generate_from_frequencies(word_counts)

        # 저장할 폴더 확인 및 생성
        if not STATIC_DIR.exists():
            logger.info(f"디렉토리 {STATIC_DIR}가 존재하지 않아 생성합니다.")
            STATIC_DIR.mkdir(parents=True, exist_ok=True)

        # 워드클라우드 이미지 저장
        image_filename = STATIC_DIR / f"{Path(filename).stem}.png"

        logger.info(f"워드클라우드 이미지를 {image_filename}로 저장 중.")
        wordcloud.to_file(str(image_filename))

        logger.info(f"워드클라우드가 {image_filename}에 저장되었습니다.")
        return str(image_filename)  # 경로를 반환합니다.

    except FileNotFoundError:
        logger.error(f"파일을 찾을 수 없습니다: {filename}")
        return None
    except json.JSONDecodeError:
        logger.error(f"JSON 파일을 디코딩하는 중 오류가 발생했습니다: {filename}")
        return None
    except ValueError as ve:
        logger.error(f"값 오류 발생: {ve}")
        return None
    except Exception as e:
        logger.error(f"알 수 없는 오류가 발생했습니다: {e}")
        return None
