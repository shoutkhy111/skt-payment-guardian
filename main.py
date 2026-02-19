import uvicorn
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List
import time
from datetime import datetime
import sys
import os

# ==========================================
# 0. 안전 모듈 로딩 (실패해도 서버는 켜짐)
# ==========================================
REAL_AI_AVAILABLE = False
try:
    # 프로젝트 루트 경로 추가
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    from backend.incident_workflow import build_incident_graph
    from langchain_core.messages import HumanMessage, ToolMessage
    REAL_AI_AVAILABLE = True
    print("✅ [Server] AI Module Loaded.")
except Exception as e:
    print(f"⚠️ [Server] AI Module Missing ({e}). Running in Simulation Mode.")
    REAL_AI_AVAILABLE = False

app = FastAPI(title="SKT Payment Guardian API")

# ==========================================
# 1. 상태 관리
# ==========================================
NODES = [
    "SKT_Gateway", "금융결제원", "KIS정보통신", "NICE정보통신",
    "신한은행", "국민은행", "우리은행", "하나은행", "농협은행",
    "삼성카드", "현대카드", "신한카드", "KB국민카드"
]

# 초기 상태
system_state = {
    "nodes": {node: "normal" for node in NODES},
    "agent_logs": [],
    "scenario": "normal",
    "is_processing": False
}

class StatusResponse(BaseModel):
    timestamp: str
    nodes: Dict[str, str]
    agent_logs: List[str]
    scenario: str
    is_processing: bool

class ScenarioRequest(BaseModel):
    scenario_type: str

# ==========================================
# 2. AI 실행 로직 (시뮬레이션 포함)
# ==========================================
def run_ai_background(scenario_type: str, error_log: str):
    system_state["is_processing"] = True
    system_state["agent_logs"] = []
    
    ts = lambda: datetime.now().strftime("%H:%M:%S")
    system_state["agent_logs"].append(f"[{ts()}] 🚀 [시스템] 장애 분석 및 대응 프로세스 시작...")

    # [Case A] 모듈이 없거나 로딩 실패 시 -> 자체 시뮬레이션 (절대 에러 안 남)
    if not REAL_AI_AVAILABLE:
        time.sleep(1)
        system_state["agent_logs"].append(f"[{ts()}] ⚠️ [시스템] AI 엔진 연동 불가. 시뮬레이션 모드로 전환.")
        
        time.sleep(1)
        system_state["agent_logs"].append(f"[{ts()}] 🚦 [라우터] 로그 분석 결과: 'Critical(심각)' 등급 판정.")
        
        time.sleep(1)
        if scenario_type == "single_failure":
            system_state["agent_logs"].append(f"[{ts()}] 🩺 [진단] '신한은행' 응답 지연(3000ms) 확인.")
            system_state["agent_logs"].append(f"[{ts()}] 🛠️ [도구] 네트워크 상태 점검(Ping) 완료.")
        else:
            system_state["agent_logs"].append(f"[{ts()}] 🩺 [진단] 다중 노드 접속 불가 확인.")
            system_state["agent_logs"].append(f"[{ts()}] 🛠️ [도구] 전체 인프라 헬스체크 수행.")

        time.sleep(1)
        system_state["agent_logs"].append(f"[{ts()}] 📚 [RAG] 에러 코드 기반 SOP 매뉴얼 검색 중...")
        system_state["agent_logs"].append(f"[{ts()}] 💡 [결과] SOP 발견: '예비 라인 전환 및 담당자 전파'.")
        
        time.sleep(1)
        system_state["agent_logs"].append(f"[{ts()}] 📨 [알림] 운영팀 및 담당자에게 SMS 발송 완료.")
        system_state["agent_logs"].append(f"[{ts()}] ✅ [완료] 장애 대응 조치가 완료되었습니다.")
        
        system_state["is_processing"] = False
        return

    # [Case B] 실제 AI 실행 (LangGraph)
    try:
        graph = build_incident_graph()
        thread_id = f"thread_{int(time.time())}"
        config = {"configurable": {"thread_id": thread_id}}
        
        inputs = {
            "messages": [HumanMessage(content="장애 로그 분석 요청")], 
            "raw_log": error_log,
            "tool_steps": [],
            "structured_report": {}
        }
        
        for event in graph.stream(inputs, config=config):
            now = ts()
            for key, value in event.items():
                if key == "triage":
                    system_state["agent_logs"].append(f"[{now}] 🚦 [라우터] 로그 유형 분석 중...")
                elif key == "tools":
                    msgs = value.get("messages", [])
                    for m in msgs:
                        if isinstance(m, ToolMessage):
                            content = m.content[:30] + "..."
                            system_state["agent_logs"].append(f"[{now}] 📚 [도구 결과] {content}")
                elif key == "diagnosis":
                    msgs = value.get("messages", [])
                    if msgs and not msgs[-1].tool_calls:
                         system_state["agent_logs"].append(f"[{now}] 🧠 [진단] 원인 분석 및 추론 중...")
                elif key == "alert_gen":
                    report = value.get("structured_report", {})
                    if report:
                        sev = report.get('severity', 'INFO')
                        system_state["agent_logs"].append(f"[{now}] 📨 [리포트] 등급: {sev}, MMS 발송 완료.")
                        system_state["agent_logs"].append(f"[{now}] ✅ [완료] 워크플로우 종료.")

    except Exception as e:
        system_state["agent_logs"].append(f"[{ts()}] ❌ [오류] AI 실행 중 예외 발생: {str(e)}")
    finally:
        system_state["is_processing"] = False

# ==========================================
# 3. API 엔드포인트
# ==========================================
@app.get("/status", response_model=StatusResponse)
def get_status():
    return StatusResponse(
        timestamp=datetime.now().strftime("%H:%M:%S"),
        nodes=system_state["nodes"],
        agent_logs=system_state["agent_logs"],
        scenario=system_state["scenario"],
        is_processing=system_state["is_processing"]
    )

@app.post("/set_scenario")
def set_scenario(req: ScenarioRequest, background_tasks: BackgroundTasks):
    system_state["scenario"] = req.scenario_type
    
    # 노드 초기화
    for n in NODES: system_state["nodes"][n] = "normal"
    
    error_log = "General Error"
    if req.scenario_type == "single_failure":
        system_state["nodes"]["신한은행"] = "error"
        error_log = "[ERROR] TIME:14:05 | BANK:Shinhan | CODE:E-503 | MSG:Service Unavailable"
    elif req.scenario_type == "triple_failure":
        system_state["nodes"]["KIS정보통신"] = "error"
        system_state["nodes"]["삼성카드"] = "error"
        system_state["nodes"]["국민은행"] = "error"
        error_log = "[CRITICAL] Multi-Fail Detected"
    elif req.scenario_type == "normal":
        system_state["agent_logs"] = [f"[{datetime.now().strftime('%H:%M:%S')}] 🟢 시스템 정상화 완료."]
        return {"status": "ok"}

    background_tasks.add_task(run_ai_background, req.scenario_type, error_log)
    return {"status": "accepted"}

if __name__ == "__main__":
    # 포트 8003
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)