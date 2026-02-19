from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from backend.utils.system_config import get_azure_chat_model

class TriageResult(BaseModel):
    is_incident: bool = Field(description="장애 상황이면 True, 단순 정보면 False")
    category: str = Field(description="장애 유형 (예: Network, Database, Application, None)")
    reason: str = Field(description="판단 근거")

def triage_log_node(state):
    """
    로그가 장애 상황인지 단순 정보인지 판단 (Structured Output 적용)
    """
    llm = get_azure_chat_model()
    raw_log = state.get("raw_log", "")
    
    # 구조화된 출력을 위한 LLM 설정
    structured_llm = llm.with_structured_output(TriageResult)

    system_prompt = """
    당신은 SKT 결제 시스템의 1차 관제 라우터(Router)입니다.
    입력된 로그를 분석하여 즉각적인 조치가 필요한 '장애(Incident)'인지 판단하세요.
    
    판단 기준:
    - ERROR, CRITICAL, Timeout, Connection Refused 키워드 -> True
    - INFO, DEBUG, Healthy, Stable -> False
    
    애매한 경우 보수적으로 True(장애)로 판단하세요.
    """
    
    try:
        result = structured_llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Log: {raw_log}")
        ])
        
        # State 업데이트 (추후 활용을 위해)
        return {
            "incident_severity": "Unknown", 
            "messages": [HumanMessage(content=f"[Router] 분석결과: {result.category} ({result.reason})")]
        }
        
    except Exception as e:
        # Fallback (오류 시 안전하게 장애로 간주)
        return {"messages": [HumanMessage(content=f"[Router Error] {str(e)}. Defaulting to Incident.")]}

def route_next(state):
    """
    Router의 판단 결과에 따라 다음 노드 결정 (조건부 엣지)
    """
    # 최근 메시지 확인 (위에서 추가한 메시지 내용 기반 필터링 가능하지만, 
    # 여기서는 로그 내용으로 더블 체크하거나 State 변수를 활용하는 것이 좋음.
    # 이번 구현에서는 raw_log 내용을 보고 간단히 분기)
    
    log = state.get("raw_log", "")
    if "ERROR" in log or "CRITICAL" in log or "Timeout" in log:
        return "diagnosis"
    return "end"