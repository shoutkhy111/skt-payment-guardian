from langchain_core.messages import SystemMessage, HumanMessage
from backend.utils.system_config import get_azure_chat_model
from backend.tools.infrastructure_tools import search_sop_manual, check_network_latency

def diagnosis_node(state):
    """
    장애 원인 진단 및 Tool 사용 계획 수립 (ReAct Pattern)
    """
    llm = get_azure_chat_model()
    
    # Tool 바인딩
    tools = [search_sop_manual, check_network_latency]
    llm_with_tools = llm.bind_tools(tools)
    
    # Few-shot 예시 및 강력한 제약조건이 포함된 시스템 프롬프트
    system_msg = """
    [Role]
    당신은 SKT 결제 시스템 장애 진단 전문가(Diagnosis Specialist)입니다.
    
    [Goal]
    주어진 로그와 도구(Tool)를 사용하여 장애의 근본 원인을 파악하고 해결책을 찾으십시오.
    
    [Constraints]
    1. 추측하지 마십시오. 반드시 Tool('search_sop_manual', 'check_network_latency')의 결과를 근거로 말하십시오.
    2. 모르는 정보는 솔직하게 "정보 부족"이라고 기술하십시오.
    3. Tool 호출이 필요하다고 판단되면 즉시 호출하십시오.
    
    [Few-Shot Examples]
    User: "E-503 Error on Shinhan Bank"
    Assistant: (Thought) 신한은행 응답 지연이 의심됩니다. 먼저 Latency를 체크하고 SOP를 검색하겠습니다. 
               (Call Tool) check_network_latency("Shinhan"), search_sop_manual("E-503")
    
    User: "System Stable"
    Assistant: 현재 시스템은 정상입니다. 추가 조치가 불필요합니다.
    """
    
    # 현재 대화 기록 가져오기
    messages = [SystemMessage(content=system_msg)] + state["messages"]
    
    # LLM 실행 (Tool Call 포함 가능)
    response = llm_with_tools.invoke(messages)
    
    return {"messages": [response]}