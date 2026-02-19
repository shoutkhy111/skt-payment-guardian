import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_dummy_data(node_name, status):
    """상세 화면용 더미 데이터 생성"""
    # 트랜잭션 추이 데이터 (최근 20분)
    now = datetime.now()
    times = [(now - timedelta(minutes=i)).strftime("%H:%M") for i in range(20, -1, -1)]
    
    if status == 'error':
        # 장애 시: 성공 급락, 실패 급증 시뮬레이션
        success = [np.random.randint(500, 600) for _ in range(15)] + [np.random.randint(0, 50) for _ in range(6)]
        fail = [np.random.randint(0, 5) for _ in range(15)] + [np.random.randint(400, 600) for _ in range(6)]
        err_msg = f"[CRITICAL] {node_name} 응답 없음 (Timeout 30000ms)\n[ERROR] Connection Refused: Port 443\n[WARN] Retry Count: 5/5 Failed"
    else:
        # 정상 시
        success = [np.random.randint(500, 700) for _ in range(21)]
        fail = [np.random.randint(0, 10) for _ in range(21)]
        err_msg = f"[INFO] Health Check: OK\n[INFO] Latency: {np.random.randint(10, 50)}ms\n[INFO] 0 Active Alerts"

    df = pd.DataFrame({'Time': times, 'Success': success, 'Failure': fail}).set_index('Time')
    
    return {
        'total': sum(success) + sum(fail),
        'success_rate': round(sum(success) / (sum(success) + sum(fail)) * 100, 2) if (sum(success)+sum(fail)) > 0 else 0,
        'today_fail': sum(fail),
        'chart_data': df,
        'log': err_msg
    }

def render_detail_page(node_name, all_nodes_status):
    """상세 화면 렌더링 메인 함수"""
    
    # 현재 노드의 상태 확인
    status = all_nodes_status.get(node_name, 'normal')
    data = generate_dummy_data(node_name, status)
    
    # 상단 네비게이션 (뒤로가기)
    col_nav, col_title = st.columns([1, 8])
    with col_nav:
        if st.button("⬅️ DASHBOARD", use_container_width=True):
            st.session_state.current_view = 'dashboard'
            st.rerun()
            
    # 타이틀 섹션
    status_color = "#ef4444" if status == "error" else "#22c55e"
    st.markdown(f"""
        <div style="background-color: #1e293b; padding: 20px; border-radius: 10px; border-left: 10px solid {status_color}; margin-bottom: 20px;">
            <h1 style="margin:0; font-size: 2em;">📊 {node_name} 상세 분석</h1>
            <span style="color: #94a3b8;">Real-time Node Monitoring System</span>
            <span style="float:right; background:{status_color}; padding: 5px 15px; border-radius:15px; font-weight:bold;">{status.upper()}</span>
        </div>
    """, unsafe_allow_html=True)

    # 1. 핵심 지표 카드 (Metrics)
    m1, m2, m3 = st.columns(3)
    
    def metric_card(label, value, color="white"):
        st.markdown(f"""
            <div style="background:#0f172a; padding:20px; border-radius:10px; border:1px solid #334155; text-align:center;">
                <div style="font-size:2.5em; font-weight:bold; color:{color};">{value}</div>
                <div style="color:#94a3b8; margin-top:5px;">{label}</div>
            </div>
        """, unsafe_allow_html=True)

    with m1: metric_card("총 트랜잭션 (Today)", f"{data['total']:,}")
    with m2: metric_card("성공률 (%)", f"{data['success_rate']}%", "#22c55e")
    with m3: metric_card("오류 발생 (건)", f"{data['today_fail']:,}", "#ef4444")

    st.divider()

    # 2. 차트 및 로그
    col_chart, col_log = st.columns([2, 1])
    
    with col_chart:
        st.subheader("📉 트랜잭션 추이 (성공 vs 실패)")
        st.line_chart(data['chart_data'], color=["#22c55e", "#ef4444"], height=300)

    with col_log:
        st.subheader("📝 실시간 시스템 로그")
        # 터미널 스타일 로그 창
        log_html = data['log'].replace('\n', '<br>')
        border_color = "#ff4b4b" if status == 'error' else "#333"
        
        st.markdown(f"""
            <div style="
                font-family: 'Courier New', monospace;
                background-color: #000;
                color: #0f0;
                padding: 15px;
                border-radius: 5px;
                border: 1px solid {border_color};
                height: 300px;
                overflow-y: auto;
                font-size: 0.85em;
                line-height: 1.5;
            ">
                <span style="color:#aaa"># tail -f /var/log/syslog</span><br>
                {log_html}
            </div>
        """, unsafe_allow_html=True)