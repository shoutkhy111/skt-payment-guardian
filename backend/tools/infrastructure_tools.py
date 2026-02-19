from langchain_core.tools import tool
from langchain_community.vectorstores import FAISS
from langchain_openai import AzureOpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import os
from datetime import datetime

# ==========================================
# 1. 고도화된 SOP 데이터 (메타데이터 포함)
# ==========================================
RAW_SOP_DATA = [
    {
        "content": """
        [E-503] Service Unavailable 대응 절차
        1. 개요: 은행/카드사 시스템 과부하로 인한 응답 지연.
        2. 진단: 
           - Ping 테스트 Latency 2000ms 이상 시 확정.
           - Connection Timeout 로그 확인.
        3. 조치:
           - 1단계: 운영팀 및 담당자에게 SMS/Slack 전파.
           - 2단계: 해당 기관 트래픽을 예비 라인으로 우회(Failover).
           - 3단계: 10분 후 트래픽 복구 시도.
        """,
        "metadata": {"source": "SOP_Network_01.pdf", "section": "E-503", "error_code": "E-503"}
    },
    {
        "content": """
        [Triple_Fail] 다중 기관 동시 장애 대응
        1. 개요: 3개 이상의 금융기관 동시 접속 불가. VAN사 게이트웨이 이슈 의심.
        2. 조치:
           - 즉시 'Critical' 등급 발령.
           - CIO 및 비상대책본부(Call 119) 소집.
           - 대고객 공지문(홈페이지/앱) 게시.
           - 재해복구센터(DR) 전환 검토.
        """,
        "metadata": {"source": "SOP_Emergency_09.pdf", "section": "Critical_Multi", "error_code": "Triple_Fail"}
    },
    {
        "content": """
        [E-408] Request Timeout (VAN 구간)
        1. 진단: KIS/NICE VAN사 응답 없음.
        2. 조치: 
           - 3회 재시도 실패 시 핫라인 연락.
           - 예비 VAN사로 즉시 라우팅 변경.
        """,
        "metadata": {"source": "SOP_VAN_Guide.pdf", "section": "E-408", "error_code": "E-408"}
    }
]

# ==========================================
# 2. Vector Store 초기화 (Chunking 적용)
# ==========================================
vector_store = None

def initialize_vector_store():
    global vector_store
    if vector_store is not None:
        return

    print(f"[{datetime.now()}] 🔄 Initializing FAISS Index with Chunking...")
    
    # 문서 객체 변환
    documents = []
    for entry in RAW_SOP_DATA:
        doc = Document(page_content=entry["content"], metadata=entry["metadata"])
        documents.append(doc)
    
    # Text Splitter 적용 (Chunking)
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    split_docs = splitter.split_documents(documents)
    
    # 임베딩 및 인덱싱
    embeddings = AzureOpenAIEmbeddings(
        model="text-embedding-3-small",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2023-05-15"
    )
    
    vector_store = FAISS.from_documents(split_docs, embeddings)
    print(f"[{datetime.now()}] ✅ FAISS Index Created with {len(split_docs)} chunks.")

# ==========================================
# 3. Tools 정의
# ==========================================
@tool
def search_sop_manual(query: str):
    """
    Search standard operating procedures (SOP) for error codes or incident types.
    Returns specific guidelines with citations.
    """
    initialize_vector_store()
    
    # Retrieval (k=3, 유사도 기반)
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(query)
    
    if not docs:
        return "관련된 SOP 문서를 찾을 수 없습니다."
    
    # 결과 포맷팅 (Citation 포함)
    result_text = ""
    for i, doc in enumerate(docs):
        meta = doc.metadata
        result_text += f"\n[문서 {i+1}] 출처: {meta.get('source')} | 섹션: {meta.get('section')}\n내용: {doc.page_content.strip()}\n"
        
    return result_text

@tool
def check_network_latency(target_node: str):
    """
    Simulate checking network latency (ping) to a specific node (Bank/VAN).
    """
    # 시뮬레이션 로직
    if "신한" in target_node:
        return {"target": target_node, "latency": "3500ms", "status": "Critical", "packet_loss": "15%"}
    elif "KIS" in target_node or "삼성" in target_node:
        return {"target": target_node, "latency": "Timeout", "status": "Down", "packet_loss": "100%"}
    else:
        return {"target": target_node, "latency": "25ms", "status": "Healthy"}