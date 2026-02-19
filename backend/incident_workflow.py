from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from backend.utils.incident_state import IncidentState
from backend.agents.triage_router import triage_log_node, route_next
from backend.agents.diagnosis_agent import diagnosis_node
from backend.agents.alert_generator import alert_generation_node
from backend.tools.infrastructure_tools import search_sop_manual, check_network_latency

def build_incident_graph():
    """
    LangGraph Workflow 구성 (Router -> Diagnosis <-> Tools -> Alert)
    """
    # 1. 그래프 초기화
    workflow = StateGraph(IncidentState)
    
    # 2. 노드 추가
    workflow.add_node("triage", triage_log_node)
    workflow.add_node("diagnosis", diagnosis_node)
    
    # ToolNode (LangGraph Prebuilt) 사용
    tool_node = ToolNode([search_sop_manual, check_network_latency])
    workflow.add_node("tools", tool_node)
    
    workflow.add_node("alert_gen", alert_generation_node)
    
    # 3. 엣지 연결
    workflow.set_entry_point("triage")
    
    # 조건부 엣지 (Router -> Diagnosis or END)
    workflow.add_conditional_edges(
        "triage",
        route_next,
        {
            "diagnosis": "diagnosis",
            "end": END
        }
    )
    
    # Diagnosis -> Tools (도구 호출 시) or Alert (완료 시)
    def should_continue(state):
        messages = state['messages']
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return "alert_gen"

    workflow.add_conditional_edges(
        "diagnosis",
        should_continue,
        {
            "tools": "tools",
            "alert_gen": "alert_gen"
        }
    )
    
    # Tools 실행 후 다시 Diagnosis로 복귀 (ReAct Loop)
    workflow.add_edge("tools", "diagnosis")
    
    # Alert 생성 후 종료
    workflow.add_edge("alert_gen", END)
    
    # 4. Checkpointer 설정 (In-Memory Persistence)
    memory = MemorySaver()
    
    return workflow.compile(checkpointer=memory)