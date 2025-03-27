from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from backend.scraper import scrape_tweets
from backend.text_processing import process_tweets
from backend.wordcloud_generator import generate_wordcloud
from mangum import Mangum
import logging
import asyncio
import os
from fastapi.staticfiles import StaticFiles
import subprocess
import sys

# FastAPI 앱 초기화
app = FastAPI()


# def install_packages():
#     """런타임에 추가 패키지를 설치하는 함수"""
#     packages = [
#         "selenium",
#         "spacy",
#         "matplotlib",
#         "nltk",
#         "pandas",
#         "wordcloud",
#         "webdriver-manager"
#     ]
#     for package in packages:
#         try:
#             subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
#             print(f"✅ {package} 설치 완료")
#         except subprocess.CalledProcessError:
#             print(f"⚠ {package} 설치 실패")

# @app.on_event("startup")
# async def startup_event():
#     install_packages()


# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app.mount("/static", StaticFiles(directory=os.path.join(os.getcwd(), "backend/static")), name="static")


# 프로젝트 경로 설정
BASE_DIR = Path(__file__).resolve().parent
TWEETS_DIR = BASE_DIR / "tweets"
STATIC_DIR = BASE_DIR / "static"

# 데이터 모델 정의
class TweetRequest(BaseModel):
    username: str
    max_tweets: int = 50

class FileNameRequest(BaseModel):
    filename: str

# 트위터 크롤링 & 워드클라우드 생성 /scrape 엔드포인트
@app.post("/scrape")
async def scrape(request: TweetRequest, background_tasks: BackgroundTasks):
    """트위터에서 트윗을 크롤링하고 JSON 파일로 저장 후 워드클라우드 자동 생성"""
    logger.info(f"트윗 크롤링 요청: {request.username}, 최대 {request.max_tweets}개")

    try:
        tweets = await asyncio.to_thread(scrape_tweets, request.username, request.max_tweets)
        if not tweets:
            logger.warning("트윗 없음")
            raise HTTPException(status_code=404, detail="트윗을 찾을 수 없습니다.")

        # 트윗 처리 후 JSON 파일 저장
        filename = process_tweets(request.username, tweets)

        # 워드클라우드 생성 비동기 처리
        background_tasks.add_task(generate_wordcloud, filename)

        # 워드클라우드 이미지 파일명 생성 후 반환
        image_filename = f"{Path(filename).stem}.png"  # .json에서 .png로 변환

        return {"message": "트윗이 저장되었으며, 워드클라우드 생성 중", "file": image_filename}

    except Exception as e:
        logger.error(f"크롤링 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {e}")

# 워드클라우드 이미지 경로 반환 /wordcloud/{filename} 엔드포인트
@app.get("/wordcloud/{filename}")
async def get_wordcloud(filename: str):
    """워드클라우드 이미지 경로 반환"""
    image_path = STATIC_DIR / filename
    
    if not image_path.exists():
        logger.error(f"워드클라우드 이미지 없음: {image_path}")
        raise HTTPException(status_code=404, detail="워드클라우드 이미지를 찾을 수 없습니다.")
    
    return {"message": "이미지가 존재합니다.", "image_path": f"static/{filename}"}


# Vercel용 Mangum 핸들러 추가
handler = Mangum(app)