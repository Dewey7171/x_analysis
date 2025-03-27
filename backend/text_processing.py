import os
import re
import json
import uuid
import datetime
from collections import Counter
from konlpy.tag import Okt
from spacy.cli import download
from nltk.corpus import stopwords
import spacy
import logging
import nltk



# 한국어 형태소 분석기
okt = Okt()

# 모델 다운로드 함수 정의
def ensure_model_installed(model_name):
    try:
        # 모델이 이미 설치되어 있으면, 로드 시도
        nlp = spacy.load(model_name)
        print(f"{model_name} 모델이 이미 설치되어 있습니다.")
    except OSError:
        # 모델이 없으면 다운로드
        print(f"{model_name} 모델이 설치되어 있지 않습니다. 다운로드 중...")
        download(model_name)
        nlp = spacy.load(model_name)
        print(f"{model_name} 모델 다운로드 완료!")

# 서버 시작 시 모델 확인 및 다운로드
ensure_model_installed("en_core_web_sm")


# 영어 NLP 모델 로드
nlp = spacy.load("en_core_web_sm")

# 로깅 설정
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


nltk.download('stopwords')
stop_words_en = set(stopwords.words('english'))

# 한국어 불용어 리스트 (추가 가능)
stop_words_ko = {"이", "그", "저", "것", "하다", "되다", "있다", "수", "을", "를", "은", "는", "이", "가", "고", "의"}

def clean_text(text):
    """트윗에서 특수 문자, 링크, 이모지 제거"""
    try:
        text = re.sub(r"http\S+|www\S+", "", text)  # URL 제거
        text = re.sub(r"[^A-Za-z가-힣 ]", "", text)  # 영어 & 한글만 남기기
        return text.lower().strip()
    except Exception as e:
        logging.error(f"clean_text 함수에서 오류 발생: {e}")
        raise

def process_tweets(username, tweets):
    """트윗 리스트를 전처리하고 주요 단어를 JSON으로 저장"""
    word_freq = Counter()  # 단어 빈도수 카운팅

    for idx, tweet in enumerate(tweets):
        try:
            clean_tweet = clean_text(tweet)  # 텍스트 전처리

            # 영어 단어 처리 (spaCy 사용)
            doc = nlp(clean_tweet)
            english_words = [
                token.lemma_ for token in doc
                if token.is_alpha and token.text not in stop_words_en  # 불용어 제거
            ]

            # 한국어 단어 처리 (Okt 사용)
            korean_words = [
                word for word, tag in okt.pos(clean_tweet, stem=True)  # 어간 추출 적용
                if word not in stop_words_ko and tag in ["Noun", "Verb", "Adjective"]  # 명사, 동사, 형용사만
            ]

            # 영어, 한국어 단어가 없는 경우 로그에 기록
            if not english_words and not korean_words:
                logging.warning(f"Tweet {idx+1} ({tweet})에서 영어 또는 한국어 단어가 추출되지 않았습니다.")

            # 단어 빈도수 업데이트
            word_freq.update(english_words + korean_words)

        except Exception as e:
            logging.error(f"process_tweets 함수에서 오류 발생: Tweet {idx+1}에서 {e}")
            continue  # 오류가 발생하면 해당 트윗을 건너뜁니다.

    # JSON 파일로 저장
    try:
        file_path = save_to_json(username, word_freq)  # 파일 경로를 반환
    except Exception as e:
        logging.error(f"save_to_json 함수에서 오류 발생: {e}")
        raise

    return file_path  # 파일 경로 반환

def save_to_json(username, word_freq):
    """결과 데이터를 /tweets/ 폴더에 JSON 파일로 저장"""
    try:
        # 저장 경로 설정
        save_dir = "tweets"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)  # tweets 폴더가 없으면 생성

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        unique_id = str(uuid.uuid4())[:8]  # 짧은 UUID 생성
        filename = f"tweets_{timestamp}_{unique_id}.json"
        file_path = os.path.join(save_dir, filename)  # 경로와 파일명 합치기

        data = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "username": username,
            "words": word_freq
        }

        # JSON 파일로 저장
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        logging.info(f"데이터가 {file_path} 에 저장되었습니다.")

    except Exception as e:
        logging.error(f"save_to_json 함수에서 오류 발생: {e}")
        raise  # 예외를 다시 발생시켜서 호출한 곳에서 처리하게 할 수 있습니다.

    return file_path  # 파일 경로 반환
