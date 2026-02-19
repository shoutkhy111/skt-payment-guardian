from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from backend.utils.system_config import get_azure_chat_model

# 1. 출력 스키마 정의 (Pydantic)
class IncidentReport(BaseModel):
    severity: str = Field(description="장애 등급 (Critical, Major, Minor)")
    location: str = Field(description="장애 발생 위치 (예: 신한은행, VAN사)")
    root_cause: str = Field(description="근본 원인 요약")
    action_items: list[str] = Field(description="구체적인 조치 항목 리스트")
    mms_text: str = Field(description="담당자 전파용 SMS 문구 (간결하게)")
    evidence: str = Field(description="판단 근거 (Tool 결과 인용)")

def alert_generation_node(state):
    """
    수집된 정보를 바탕으로 구조화된 장애 리포트 생성
    """
    llm = get_azure_chat_model()
    structured_llm = llm.with_structured_output(IncidentReport)
    
    messages = state["messages"]
    
    system_prompt = """
    당신은 장애 전파 책임자(Alert Manager)입니다.
    이전 단계에서 진단 에이전트가 수집한 정보를 바탕으로 최종 리포트를 작성하세요.
    
    [작성 규칙]
    1. Severity는 Critical, Major, Minor 중 하나로 선택.
    2. MMS 문구는 "[SKT 장애알림]"으로 시작하며, 80자 이내로 핵심만 요약.
    3. 조치 항목(Action Items)은 SOP에 기반하여 구체적으로 작성.
    """
    
    try:
        # LLM 호출
        report = structured_llm.invoke([SystemMessage(content=system_prompt)] + messages)
        
        # State에 구조화된 데이터 저장
        return {
            "structured_report": report.dict(),
            "final_action_plan": f"[{report.severity}] {report.location} - {report.root_cause}\n조치: {', '.join(report.action_items)}",
            "incident_severity": report.severity,
            "messages": [HumanMessage(content=f"최종 리포트 생성 완료: {report.mms_text}")]
        }
        
    except Exception as e:
        # Fallback (구조화 실패 시)
        error_report = {
            "severity": "Unknown",
            "location": "Unknown",
            "root_cause": "Analysis Failed",
            "action_items": ["Manual Check Required"],
            "mms_text": f"[SKT 장애알림] 분석 실패. 수동 점검 요망. ({str(e)})",
            "evidence": "N/A"
        }
        return {
            "structured_report": error_report,
            "final_action_plan": "분석 실패 (수동 점검 필요)",
            "incident_severity": "Unknown",
             "messages": [HumanMessage(content="리포트 생성 중 오류 발생")]
        }