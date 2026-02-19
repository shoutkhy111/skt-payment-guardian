from typing import TypedDict, Annotated, List, Dict, Any
from langchain_core.messages import BaseMessage
import operator

class IncidentState(TypedDict):
    # 메시지 기록 (append 방식)
    messages: Annotated[List[BaseMessage], operator.add]
    
    # 원본 로그
    raw_log: str
    
    # 도구 실행 결과 누적 (근거 확보용)
    tool_steps: List[Dict[str, Any]]
    
    # 최종 구조화된 리포트 (JSON)
    structured_report: Dict[str, Any]
    
    # 최종 조치 계획 (UI 표시용 문자열)
    final_action_plan: str
    
    # 장애 심각도
    incident_severity: str