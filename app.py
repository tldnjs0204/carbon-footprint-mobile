import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정 - 모바일 세로 모드 최적화
st.set_page_config(
    page_title="🌍 탄소배출 대시보드",
    page_icon="📱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. 디자인 및 카드 스타일 완벽 복구
st.markdown("""
<style>
    body { font-family: 'Segoe UI', sans-serif; background-color: #F9FCF9; }
    .rounded-card {
        background: white; border-radius: 18px; padding: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04); margin: 10px 0;
        border: 2px solid #A3C9AE;
    }
    .metric-card {
        background: linear-gradient(135deg, #34624C 0%, #A3C9AE 100%);
        border-radius: 18px; padding: 18px; color: white;
        text-align: center; margin: 10px 0;
    }
    .block-container { padding-top: 2rem !important; }
</style>
""", unsafe_allow_html=True)

st.title("🌍여행 탄소발자국 대시보드")
st.markdown("---")

# 3. 데이터 및 계산
ANNUAL_CARBON_BUDGET_KG = 5900.0
data = {
    "교통수단": ["지하철 / 전기열차", "고속열차 (KTX/SRT)", "시내버스", "고속/시외버스", "전기 승용차 (BEV)", "하이브리드 승용차", "가솔린 승용차", "디젤 승용차", "국내선 항공기"],
    "1km당 CO2 배출량(g)": [6, 14, 28, 33, 40, 90, 150, 170, 255],
    "평균시속(km/h)": [40, 200, 20, 80, 35, 35, 35, 35, 600],
    "카테고리": ["대중교통", "대중교통", "대중교통", "대중교통", "개인교통", "개인교통", "개인교통", "개인교통", "항공"]
}
df = pd.DataFrame(data)
df["1시간당 배출량(g)"] = df["평균시속(km/h)"] * df["1km당 CO2 배출량(g)"]

# 입력칸 (모바일 최적화)
selected_transport = st.selectbox("1️⃣ 이용할 교통수단 선택:", df["교통수단"].tolist(), index=1)
time_hours = st.slider("2️⃣ 1회 이동 시간 (시간):", 0.5, 6.0, 2.5, step=0.5)
frequency_per_trip = st.slider("3️⃣ 이용 횟수:", 1, 4, 2)

selected_row = df.loc[df["교통수단"] == selected_transport].iloc[0]
total_emission_kg = (selected_row["1시간당 배출량(g)"] * time_hours * frequency_per_trip) / 1000

# 4. 결과 요약
st.subheader(f"📊 '{selected_transport}' 결과")
st.metric("이번 여행 총 배출량", f"{total_emission_kg:,.2f} kg CO₂")
st.metric("상쇄 소나무", f"약 {(total_emission_kg / 6.6):,.2f} 그루")
st.markdown("---")

# 5. 연간 예산 비율
remaining = max(0.0, ANNUAL_CARBON_BUDGET_KG - total_emission_kg)
fig_pie = px.pie(values=[total_emission_kg, remaining], names=["배출량", "잔여"], color_discrete_sequence=["#F2C4B1", "#34624C"], hole=0.4)
st.plotly_chart(fig_pie, use_container_width=True)

# 6. 수단 비교 그래프
st.subheader("💡 수단별 비교")
df["비교배출량(g)"] = df["1시간당 배출량(g)"] * time_hours
fig_bar = px.bar(df.sort_values("비교배출량(g)"), x="비교배출량(g)", y="교통수단", color="카테고리", 
                 color_discrete_map={"대중교통":"#34624C", "개인교통":"#E0E8A5", "항공":"#F2C4B1"}, orientation='h')
st.plotly_chart(fig_bar, use_container_width=True)

# 7. 감축 효과 (오류 해결 및 친환경 선택 시 숨김 로직 포함)
st.subheader("🌱 전환 시 감축 효과")
train_row = df.loc[df["교통수단"] == "고속열차 (KTX/SRT)"].iloc[0]
reduction_kg = total_emission_kg - (train_row["1시간당 배출량(g)"] * time_hours * frequency_per_trip / 1000)

if selected_transport in ["고속열차 (KTX/SRT)", "지하철 / 전기열차"]:
    st.markdown("""<div style="background-color: #F8FCF8; border: 2px solid #A3C9AE; padding: 20px; border-radius: 18px; text-align: center;">🎉 지구를 살리는 최고의 선택입니다!</div>""", unsafe_allow_html=True)
else:
    # 큰따옴표 문법 오류를 방지하기 위해 작은따옴표(') 사용
    st.success(f"🎉 동일 거리를 **'고속열차(KTX/SRT)'**로 전환 시, **{reduction_kg:,.2f} kg CO₂**를 줄일 수 있습니다!\n\n(연간 탄소 예산의 **{(reduction_kg / ANNUAL_CARBON_BUDGET_KG)*100:.2f}%** 절약)")
    
    compare_df = pd.DataFrame({"구분": ["현재", "전환"], "배출량(kg)": [total_emission_kg, total_emission_kg - reduction_kg]})
    st.plotly_chart(px.pie(compare_df, names="구분", values="배출량(kg)", color_discrete_sequence=["#F2C4B1", "#A3C9AE"], hole=0.4), use_container_width=True)

st.caption("📱 모바일 최적화 대시보드 | 탄소여권 프로젝트")
