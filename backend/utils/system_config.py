import os
from dotenv import load_dotenv

load_dotenv()

class SystemConfig:
    # 1. Azure 기본 설정
    AZURE_ENDPOINT = os.getenv("AOAI_ENDPOINT")
    API_KEY = os.getenv("AOAI_API_KEY")
    # Azure API 버전 (GPT-4o 계열은 최신 버전 권장)
    API_VERSION = "2024-05-01-preview"
    
    # 2. 모델 배포명 (Deployment Name) 매핑
    # 속도가 빠른 mini 모델을 메인으로 사용
    MODEL_DEPLOYMENT = os.getenv("AOAI_DEPLOY_GPT4O_MINI") 
    
    # 3. 임베딩 모델 배포명 매핑
    # 비용 효율적인 3-small 사용
    EMBEDDING_DEPLOYMENT = os.getenv("AOAI_DEPLOY_EMBED_3_SMALL")

    # 필수값 체크
    if not AZURE_ENDPOINT or not API_KEY:
        raise ValueError("⚠️ .env 파일에 AOAI_ENDPOINT 또는 AOAI_API_KEY가 없습니다.")