import streamlit as st
import graphviz
import requests
import time
import sys
import os

# ==========================================
# 0. 설정
# ==========================================
# 상세화면 모듈 로딩 시도 (없어도 안 죽음)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from monitoring_view_detail import render_detail_page
except ImportError:
    try:
        from dashboard.monitoring_view_detail import render_detail_page
    except ImportError:
        render_detail_page = None

st.set_page_config(page_title="SKT Payment Guardian", layout="wide", initial_sidebar_state="collapsed")
API_URL = "http://localhost:8003"

# ==========================================
# 1. 스타일
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #0b1120; color: #e2e8f0; }
    .dashboard-header {
        background: linear-gradient(90deg, #0f172a 0%, #1e3a8a 100%);
        padding: 20px; border-radius: 10px; border: 1px solid #334155;
        display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;
    }
    div.stButton > button {
        background-color: #1e293b; color: #f1f5f9; border: 1px solid #475569;
        border-radius: 8px; height: 50px; font-weight: 600;
    }
    div.stButton > button:hover {
        background-color: #334155; border-color: #38bdf8; color: #38bdf8;
    }
    .agent-terminal {
        background-color: #0d1117; color: #58a6ff; font-family: 'Consolas', monospace;
        padding: 15px; border-radius: 8px; border: 1px solid #30363d;
        height: 300px; overflow-y: auto; font-size: 0.85em; line-height: 1.6;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 통신 (무한 로딩 해결)
# ==========================================
def fetch_status():
    try:
        # 1초 안에 응답 없으면 바로 에러 처리 (무한 대기 방지)
        res = requests.get(f"{API_URL}/status", timeout=1.0)
        if res.status_code == 200:
            return res.json()
    except Exception:
        return None
    return None

def trigger_scenario(stype):
    try:
        requests.post(f"{API_URL}/set_scenario", json={"scenario_type": stype}, timeout=1.0)
        st.toast("🚀 명령 전달 완료", icon="✅")
    except:
        st.toast("⚠️ 백엔드 연결 실패", icon="❌")

# ==========================================
# 3. 토폴로지
# ==========================================
def render_topology(nodes_status):
    dot = graphviz.Digraph()
    dot.attr(bgcolor='transparent', rankdir='TB', splines='curved', nodesep='0.6', ranksep='0.8')
    dot.attr('node', shape='box', style='filled, rounded', fontname="Sans-Serif", fontcolor='white', penwidth='0', margin='0.2')
    dot.attr('edge', color='#cbd5e1', arrowhead='vee', arrowsize='0.8', penwidth='1.2')
    
    C_OK = '#0f766e'; C_ERR = '#b91c1c'; C_GW = '#1e40af'
    
    def get_attr(n): return {'fillcolor': C_ERR} if nodes_status.get(n) == "error" else {'fillcolor': C_OK}
    def get_edge(t): return {'color': '#f87171', 'penwidth': '3.0', 'style': 'dashed'} if nodes_status.get(t) == 'error' else {'color': '#cbd5e1', 'style': 'solid'}

    dot.node('GW', 'SKT_Gateway', fillcolor=C_GW)
    with dot.subgraph(name='mid'):
        c = dot
        for n in ["금융결제원", "KIS정보통신", "NICE정보통신"]: c.node(n, n, **get_attr(n))
    with dot.subgraph(name='bot'):
        c = dot
        for n in ["신한은행", "국민은행", "우리은행", "삼성카드", "현대카드"]: c.node(n, n, **get_attr(n))

    dot.edge('GW', '금융결제원'); dot.edge('GW', 'KIS정보통신'); dot.edge('GW', 'NICE정보통신')
    dot.edge('금융결제원', '신한은행', **get_edge('신한은행'))
    dot.edge('금융결제원', '국민은행', **get_edge('국민은행'))
    dot.edge('금융결제원', '우리은행')
    dot.edge('KIS정보통신', '삼성카드', **get_edge('삼성카드'))
    dot.edge('NICE정보통신', '현대카드')
    return dot

# ==========================================
# 4. 메인 루프
# ==========================================
def main():
    if 'current_view' not in st.session_state: st.session_state.current_view = 'dashboard'
    if 'selected_node' not in st.session_state: st.session_state.selected_node = None

    # 데이터 가져오기 (실패 시 None)
    data = fetch_status()

    # [중요] 연결 실패 시 무한 로딩 대신 에러 화면 표시
    if not data:
        st.error("🚨 백엔드 연결 실패 (Port 8003)")
        st.warning("터미널 A에서 서버를 실행해주세요: `uvicorn main:app --host 0.0.0.0 --port 8003`")
        if st.button("🔄 연결 재시도"): st.rerun()
        return

    # 상세 화면 처리
    if st.session_state.current_view == 'detail':
        if render_detail_page:
            render_detail_page(st.session_state.selected_node, data['nodes'])
        else:
            st.error("상세 화면 모듈을 찾을 수 없습니다.")
            if st.button("돌아가기"): st.session_state.current_view = 'dashboard'; st.rerun()
        return

    # 대시보드 화면
    st.markdown(f"""
        <div class="dashboard-header">
            <div><h2 style="margin:0;">🛡️ SKT Payment Guardian</h2></div>
            <div style="text-align:right;">
                <div style="font-size:24px; font-weight:bold; color:#38bdf8;">{data['timestamp']}</div>
                <div style="color:#22c55e;">● SYSTEM ONLINE</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col_map, col_ctrl = st.columns([2, 1.2])

    with col_map:
        st.subheader("📡 실시간 토폴로지")
        st.graphviz_chart(render_topology(data['nodes']), use_container_width=True)

    with col_ctrl:
        st.subheader("🧠 AI 에이전트 로그")
        logs_html = ""
        for log in data['agent_logs']:
            c = "#58a6ff"
            if "🚀" in log: c = "#d2a8ff"
            elif "🛠️" in log: c = "#e2b93d"
            elif "✅" in log: c = "#7ee787"
            elif "❌" in log: c = "#ff7b72"
            logs_html += f"<div style='color:{c}; margin-bottom:4px;'>{log}</div>"
            
        if data['is_processing']:
            logs_html += "<div style='color:#8b949e; animation: blink 1s infinite;'>_ AI 분석 진행 중...</div>"

        st.markdown(f"<div class='agent-terminal'>{logs_html}</div>", unsafe_allow_html=True)
        
        st.divider()
        st.subheader("🎮 제어 패널")
        c1, c2, c3 = st.columns(3)
        if c1.button("🟢 정상화"): trigger_scenario("normal")
        if c2.button("🟠 1개 장애"): trigger_scenario("single_failure")
        if c3.button("🔴 3개 장애"): trigger_scenario("triple_failure")
        
        st.divider()
        st.subheader("🚦 상세 상태 확인")
        sorted_nodes = sorted(data['nodes'].items(), key=lambda x: 0 if x[1]=='error' else 1)
        for i in range(0, len(sorted_nodes), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(sorted_nodes):
                    n, s = sorted_nodes[i+j]
                    btn_label = f"{'🚨' if s=='error' else '✅'} {n}"
                    if cols[j].button(btn_label, key=n, use_container_width=True):
                        st.session_state.selected_node = n
                        st.session_state.current_view = 'detail'
                        st.rerun()

    time.sleep(1)
    st.rerun()

if __name__ == "__main__":
    main()