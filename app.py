import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="탄소여권",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    body { font-family: 'Segoe UI', sans-serif; background-color: #F9FCF9; }
    .rounded-card {
        background: white; border-radius: 18px; padding: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04); margin: 10px 0;
        border: 2px solid #A3C9AE;
    }
    .result-box {
        background: linear-gradient(135deg, #34624C 0%, #52B788 100%);
        border-radius: 18px; padding: 20px; color: white;
        text-align: center; margin: 16px 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #34624C 0%, #A3C9AE 100%);
        border-radius: 18px; padding: 18px; color: white;
        text-align: center; margin: 10px 0;
    }
    .block-container { padding-top: 2rem !important; }
    .section-title { font-size: 1.1rem; font-weight: 700; color: #34624C; margin-top: 1.5rem; }
    .note { font-size: 0.78rem; color: #888; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

ANNUAL_BUDGET_KG = 5900.0

data = {
    "교통수단": [
        "지하철 / 전기열차", "고속열차 (KTX/SRT)", "시내버스",
        "고속/시외버스", "전기 승용차 (BEV)", "하이브리드 승용차",
        "가솔린 승용차", "디젤 승용차", "국내선 항공기"
    ],
    "1km당 CO2 배출량(g)": [6, 14, 28, 33, 40, 90, 150, 170, 255],
    "평균시속(km/h)": [40, 200, 20, 80, 35, 35, 35, 35, 600],
    "카테고리": [
        "대중교통", "대중교통", "대중교통", "대중교통",
        "개인교통", "개인교통", "개인교통", "개인교통", "항공"
    ]
}
df_all = pd.DataFrame(data)
df_all["1시간당 배출량(g)"] = df_all["평균시속(km/h)"] * df_all["1km당 CO2 배출량(g)"]

transport_score_map = {
    "지하철 / 전기열차":  40  * 6   / 1000,
    "고속열차 (KTX/SRT)": 3.2,
    "시내버스":            20  * 28  / 1000,
    "고속/시외버스":       2.5,
    "전기 승용차 (BEV)":  1.5,
    "하이브리드 승용차":   35  * 90  / 1000,
    "가솔린 승용차":       5.25,
    "디젤 승용차":         5.95,
    "국내선 항공기":       600 * 255 / 1000,
}

CAR_SCORE_PER_HOUR = transport_score_map["가솔린 승용차"]

# KTX보다 배출량이 같거나 낮은 수단 → "최고의 선택" 표시
LOW_CARBON = {"지하철 / 전기열차", "시내버스", "고속열차 (KTX/SRT)"}

COLOR_MAP = {
    "대중교통": "#34624C",
    "개인교통": "#E0E8A5",
    "항공":     "#F2C4B1"
}

st.title("🌍 여행 탄소발자국 대시보드")
st.markdown("---")
