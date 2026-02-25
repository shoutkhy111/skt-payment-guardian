# 🛡️ SKT Payment Guardian (실시간 결제 장애 대응 AI 에이전트)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Tech](https://img.shields.io/badge/AI-Azure%20OpenAI-green)
![Framework](https://img.shields.io/badge/Framework-LangGraph%20%7C%20LangChain-orange)

## 📌 프로젝트 개요
**SKT Payment Guardian**은 실시간 결제 및 수납 시스템에서 발생하는 장애 로그를 **AI Agent**가 실시간으로 모니터링하고 분석하여, **운영 담당자에게 최적의 조치 가이드를 제공하는 자동화 시스템**입니다.

기존의 단순 키워드 매칭 방식 관제 시스템의 한계를 넘어, **LLM(Large Language Model)**과 **RAG(Retrieval-Augmented Generation)** 기술을 활용해 장애의 문맥을 이해하고 사내 표준 운영 절차(SOP)에 기반한 대응책을 제시합니다.

---

## 🚀 핵심 기능

### 1. Multi-Agent 협업 구조 (LangGraph)
단일 에이전트가 아닌, 역할이 세분화된 에이전트들이 유기적으로 협업합니다.
- **Triage Router**: 인입된 텍스트가 시스템 로그인지 일반 대화인지 분류
- **Diagnosis Agent (진단반)**: 장애 로그 분석 및 원인 추론 (ReAct 패턴 적용)
- **Infrastructure Tools (도구)**: 가상 망(Bank, VAN) 상태 점검 및 SOP 매뉴얼 검색
- **Alert Generator (전파반)**: 분석 결과를 바탕으로 상황 등급(Critical/Warning) 산정 및 MMS 문구 작성

### 2. RAG 기반 지식 참조 (Azure OpenAI Embeddings)
- 사내 장애 대응 매뉴얼(SOP)을 벡터 DB(FAISS)에 임베딩하여, LLM이 할루시네이션 없이 정확한 규정에 따라 대응하도록 설계되었습니다.

### 3. 실시간 관제 대시보드 (Streamlit)
- 운영자가 직관적으로 로그를 시뮬레이션하고, AI의 사고 과정(Chain of Thought)을 실시간으로 확인할 수 있는 UI를 제공합니다.

---

## 🏗️ 시스템 아키텍처

```mermaid
graph LR
    User[운영자/시스템] -->|Log Input| Router{Triage Router}
    Router -->|Log Detected| Diagnosis[Diagnosis Agent]
    Router -->|Chat| EndNode
    
    subgraph "Reasoning Loop (ReAct)"
        Diagnosis <-->|Check Health / Search SOP| Tools[Infrastructure Tools]
    end
    
    Diagnosis -->|Analysis Complete| Alert[Alert Generator]
    Alert -->|MMS & Report| Dashboard[Monitoring UI]

### 1. 시스템 전체 구조도
![시스템 전체 구조도](./images/SKT_payment_guardian_구조.jpg)

### 2. Multi-Agent 구성도 (LangGraph)
![멀티 에이전트 구성도](./images/SKT_payment_guardian_diagram.jpg)    


## 📸 실행 화면 (ScreenShots)

### 1. 통합 관제 대시보드 메인 화면
![대시보드 메인 화면](./images/SKT_payment_guardian_스크린샷1.jpg)

### 2. 장애 진단 AI 에이전트 동작(CoT) 로그
![에이전트 동작 화면](./images/SKT_payment_guardian_스크린샷2.jpg)    