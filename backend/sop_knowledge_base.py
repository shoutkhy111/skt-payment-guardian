from langchain_core.documents import Document
from langchain_openai import AzureOpenAIEmbeddings  # [변경] Azure 전용 클래스
from langchain_community.vectorstores import FAISS
from backend.utils.system_config import SystemConfig

def load_sop_documents():
    """SKT 결제 시스템 장애 대응 매뉴얼(SOP) 데이터"""
    sop_data = [
        "[장애코드 E-503] 신한은행망 점검 중. (조치: 운영팀 010-1234-5678 공지 발송 후 대기)",
        "[장애코드 E-408] VAN사(KIS) 응답 타임아웃. (조치: 3회 재시도 실패 시 핫라인 연락 및 우회 경로 활성화)",
        "[장애코드 E-999] DB Connection Pool 포화. (조치: WAS 재기동 및 긴급 증설 요청)",
        "[규정] 야간(22:00~06:00) Critical 등급 장애 발생 시 C-Level 즉시 보고 원칙."
    ]
    return [Document(page_content=m, metadata={"source": "SKT_Payment_SOP"}) for m in sop_data]

_retriever_instance = None

def get_sop_retriever():
    """Azure OpenAI 기반 FAISS 검색기 반환"""
    global _retriever_instance
    if _retriever_instance is None:
        docs = load_sop_documents()
        
        # [수정] Azure Embeddings 설정
        embeddings = AzureOpenAIEmbeddings(
            azure_deployment=SystemConfig.EMBEDDING_DEPLOYMENT,
            openai_api_version=SystemConfig.API_VERSION,
            azure_endpoint=SystemConfig.AZURE_ENDPOINT,
            api_key=SystemConfig.API_KEY,
        )
        
        # requirements.txt에 faiss-cpu 포함됨
        vectorstore = FAISS.from_documents(docs, embeddings)
        _retriever_instance = vectorstore.as_retriever()
    return _retriever_instance