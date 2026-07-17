import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. 페이지 설정 - 모바일 세로 모드 최적화 (centered & sidebar 숨김)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="교통수단별 탄소배출 대시보드",
    page_icon="📱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# 2. CSS - 참고 사진 100% 반영 딥 포레스트 그린 & 부드러운 파스텔 테마 (모바일 최적화)
# -----------------------------------------------------------------------------
# - 포인트 진녹색(딥 포레스트 그린): #34624C
# - 차분한 세이지/민트 그린: #A3C9AE
# - 부드러운 레몬 옐로우: #E0E8A5
# - 은은한 파스텔 피치/살몬: #F2C4B1
st.markdown("""
<style>
    body { 
        font-family: 'Segoe UI', sans-serif;
        background-color: #F9FCF9;
    }
    /* 모바일에서 카드 양옆 여백 및 모서리 둥글게 */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 2px solid #A3C9AE;
        padding: 16px 18px;
        border-radius: 18px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.03);
        margin-bottom: 10px;
    }
    .rounded-box {
        background: white;
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        margin: 12px 0;
        border: 2px solid #A3C9AE;
    }
    /* 모바일 화면 상하단 여백 최적화 */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
    }
</style>
""", unsafe_allow_html=True)

# 제목 및 소개
st.title("🌍 모바일 탄소발자국 대시보드")
st.markdown("**📱 이번 여행의 이동 수단과 시간을 선택하여 탄소 배출량과 1.5도씨 라이프스타일 예산을 계산해보세요!**")
st.markdown("---")

# -----------------------------------------------------------------------------
# 3. 기초 데이터 및 탄소 예산 기준치 설정 (녹색전환연구소 기준 5.9톤)
# -----------------------------------------------------------------------------
ANNUAL_CARBON_BUDGET_KG = 5900.0

data = {
    "교통수단": [
        "지하철 / 전기열차", 
        "고속열차 (KTX/SRT)", 
        "시내버스", 
        "고속/시외버스", 
        "전기 승용차 (BEV)",      # <-- 순수 전기차 완벽 추가!
        "하이브리드 승용차", 
        "가솔린 승용차", 
        "디젤 승용차", 
        "국내선 항공기"
    ],
    "1km당 CO2 배출량(g)": [6, 14, 28, 33, 40, 90, 150, 170, 255],
    "평균시속(km/h)": [40, 200, 20, 80, 35, 35, 35, 35, 600],
    "카테고리": ["대중교통", "대중교통", "대중교통", "대중교통", "개인교통", "개인교통", "개인교통", "개인교통", "항공"]
}

df = pd.DataFrame(data)
df["1시간당 배출량(g)"] = df["평균시속(km/h)"] * df["1km당 CO2 배출량(g)"]

# -----------------------------------------------------------------------------
# 4. [모바일 최적화 입력칸] 교통수단 & 이동시간 직접 선택 (본문 상단 배치)
# -----------------------------------------------------------------------------
st.markdown("""
<div style="background-color: #34624C; color: white; padding: 12px 18px; border-radius: 12px; margin-bottom: 15px; font-weight: bold; text-align: center;">
    🚗 나의 여행 정보 입력하기
</div>
""", unsafe_allow_html=True)

# 모바일에서 접근성 좋게 사이드바 대신 본문에 바로 배치
selected_transport = st.selectbox(
    "1️⃣ 이용할 교통수단을 선택하세요:",
    df["교통수단"].tolist(),
    index=1  # 기본값: 고속열차 (KTX/SRT)
)

time_hours = st.slider("2️⃣ 1회 이동 시간 (편도 기준, 시간):", 0.5, 6.0, 2.5, step=0.5)
frequency_per_trip = st.slider("3️⃣ 이용 횟수 (편도 탑승 기준):", 1, 10, 2)

# 선택된 교통수단의 데이터 조회 및 계산
selected_row = df.loc[df["교통수단"] == selected_transport].iloc[0]
avg_speed = selected_row["평균시속(km/h)"]
emission_per_hour = selected_row["1시간당 배출량(g)"]

estimated_distance_km = avg_speed * time_hours
single_trip_emission_g = emission_per_hour * time_hours
total_emission_g = single_trip_emission_g * frequency_per_trip
total_emission_kg = total_emission_g / 1000  # kg 변환

budget_percentage_total = (total_emission_kg / ANNUAL_CARBON_BUDGET_KG) * 100
trees_needed = total_emission_kg / 6.6

st.markdown("---")

# -----------------------------------------------------------------------------
# 5. [결과 요약] 스마트폰 세로 모드에 깨지지 않는 세로형 지표 카드
# -----------------------------------------------------------------------------
st.subheader(f"📊 '{selected_transport}' 여행 탄소발자국 결과")
st.caption(f"💡 평균 시속 {avg_speed}km/h 기준, 1회당 약 {estimated_distance_km:,.1f}km 이동한 것으로 계산됩니다.")

# 모바일 세로 모드에서 글자 겹침을 방지하기 위해 1줄씩 깔끔하게 쌓기
st.metric(label="🔹 편도 1회 이동 시 배출량", value=f"{single_trip_emission_g:,.0f} g CO₂")
st.metric(label=f"🔸 이번 여행 총 예상 배출량 (총 {frequency_per_trip}회)", value=f"{total_emission_kg:,.2f} kg CO₂")
st.metric(
    label="🌲 상쇄를 위해 필요한 소나무", 
    value=f"약 {trees_needed:,.2f} 그루",
    delta="이번 여행 배출량 기준",
    delta_color="off"
)

st.markdown("---")

# -----------------------------------------------------------------------------
# 6. 연간 허용량 대비 소진율 원형 그래프 (참고 사진 팔레트)
# -----------------------------------------------------------------------------
st.subheader("🎯 연간 허용 탄소배출량 중 이번 여행 사용 비율")
st.markdown("**녹색전환연구소 2030년 감축 목표 기준** 1인당 연간 허용 배출량은 **5.9톤 (5,900 kg CO₂)** 입니다.")

remaining_budget_kg = max(0.0, ANNUAL_CARBON_BUDGET_KG - total_emission_kg)
pie_data = pd.DataFrame({
    "구분": ["이번 여행 배출량", "연간 잔여 허용량"],
    "배출량(kg)": [total_emission_kg, remaining_budget_kg]
})

# [차트 1 색상] 파스텔 피치/살몬(#F2C4B1) vs 딥 포레스트 진녹색(#34624C)
fig_budget_pie = px.pie(
    pie_data,
    names="구분",
    values="배출량(kg)",
    color="구분",
    color_discrete_sequence=["#F2C4B1", "#34624C"],
    hole=0.4
)
fig_budget_pie.update_traces(
    textinfo='percent+label',
    hoverinfo='label+value',
    textfont_size=13,
    marker=dict(line=dict(color='#FFFFFF', width=2))
)
fig_budget_pie.update_layout(
    showlegend=True,
    margin=dict(l=0, r=0, t=10, b=10),
    height=280,
    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
)
st.plotly_chart(fig_budget_pie, use_container_width=True)

# 텍스트 설명 박스
st.markdown(f"""
<div class="rounded-box">
    <h4 style="margin-top:0; color:#34624C;">💡 내 탄소 예산에 미치는 영향</h4>
    <p style="font-size:0.95rem; line-height:1.5;">
        이 여행 단 한 번으로 2030년 1인당 연간 목표 배출량(<b>5,900 kg CO₂</b>)의 <b>{budget_percentage_total:.2f}%</b>를 사용하게 됩니다.
    </p>
</div>
""", unsafe_allow_html=True)

if budget_percentage_total < 1.0:
    st.success("🌿 **아주 훌륭한 저탄소 여행입니다!** 연간 허용량의 1% 미만을 사용하여 2030년 기후 목표 달성에 큰 도움이 됩니다.")
elif budget_percentage_total < 5.0:
    st.warning("⛅ **적절한 수준의 탄소 사용입니다.** 하지만 더 잦은 장거리 여행 시 기차 등 친환경 이동수단 전환을 권장합니다.")
else:
    st.error("🚨 **연간 예산 대비 배출량이 높은 편입니다!** 고속열차(KTX/SRT) 등 대중교통으로 전환하면 배출량을 획기적으로 줄일 수 있습니다.")

st.progress(min(budget_percentage_total / 100.0, 1.0))
st.markdown("---")

# -----------------------------------------------------------------------------
# 7. 9개 교통수단 전체 배출량 비교 (모바일 화면 폭 최적화 막대 그래프)
# -----------------------------------------------------------------------------
st.subheader(f"💡 동일 시간(편도 {time_hours}시간) 이동 시 CO₂ 배출량 비교")
st.caption("다른 교통수단을 이용했을 때의 배출량을 한눈에 비교해보세요!")

pastel_color_map = {
    "대중교통": "#34624C",   # 딥 포레스트 진녹색
    "개인교통": "#E0E8A5",   # 부드러운 레몬 옐로우
    "항공": "#F2C4B1"        # 은은한 파스텔 피치
}

df["선택시간당 배출량(g)"] = df["1시간당 배출량(g)"] * time_hours

fig_bar = px.bar(
    df.sort_values("선택시간당 배출량(g)", ascending=True),
    x="선택시간당 배출량(g)",
    y="교통수단",
    color="카테고리",
    color_discrete_map=pastel_color_map,
    orientation='h',
    text="선택시간당 배출량(g)",
    height=450
)

fig_bar.update_traces(
    texttemplate='%{text:,.0f} g', 
    textposition='outside', 
    marker_line_color='rgb(255,255,255)', 
    marker_line_width=1.5,
    cliponaxis=False
)
fig_bar.update_layout(
    xaxis_title="CO₂ 배출량 (g)",
    yaxis_title="",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="white",
    margin=dict(l=0, r=35, t=20, b=0),
    legend=dict(title="분류", orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
)

st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 8. 친환경 열차 전환 시 감축 효과 원형 그래프
# -----------------------------------------------------------------------------
st.subheader("🌱 친환경 열차 전환 시 감축 효과")
st.markdown(f"이번 여행에서 **{selected_transport}**(으)로 총 **{total_emission_kg:,.2f} kg**의 탄소를 배출하게 됩니다.")

train_row = df.loc[df["교통수단"] == "고속열차 (KTX/SRT)"].iloc[0]
train_total_kg = (train_row["1km당 CO2 배출량(g)"] * estimated_distance_km * frequency_per_trip) / 1000
reduction_kg = total_emission_kg - train_total_kg

if reduction_kg > 0:
    st.success(f"🎉 동일 거리를 **고속열차(KTX/SRT)**로 전환할 경우, **{reduction_kg:,.2f} kg CO₂**를 줄일 수 있습니다!\n\n(연간 탄소 예산의 **{(reduction_kg / ANNUAL_CARBON_BUDGET_KG)*100:.2f}%** 절약 효과)")
else:
    st.info("👍 이미 아주 친환경적인 대중교통 수단을 이용해 여행하고 계십니다! 훌륭합니다!")

compare_df = pd.DataFrame({
    "구분": [f"현재 선택 ({selected_transport})", "고속열차 전환 시"],
    "총 배출량(kg)": [total_emission_kg, train_total_kg]
})

# [차트 2 색상] 은은한 파스텔 피치/살몬(#F2C4B1) & 차분한 세이지 그린(#A3C9AE)
fig_pie_train = px.pie(
    compare_df, 
    names="구분", 
    values="총 배출량(kg)",
    color="구분",
    color_discrete_sequence=["#F2C4B1", "#A3C9AE"],
    hole=0.4
)
fig_pie_train.update_traces(
    marker=dict(line=dict(color='#FFFFFF', width=2)),
    textinfo='percent+label',
    textfont_size=13
)
fig_pie_train.update_layout(
    margin=dict(l=0, r=0, t=10, b=10), 
    height=280,
    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
)
st.plotly_chart(fig_pie_train, use_container_width=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 9. 하단 상세 데이터 테이블 및 참고문헌
# -----------------------------------------------------------------------------
with st.expander("📋 상세 데이터 표 보기 및 참고문헌"):
    display_df = df[["교통수단", "카테고리", "평균시속(km/h)", "1km당 CO2 배출량(g)", "1시간당 배출량(g)"]].copy()
    display_df["1시간당 배출량(g)"] = display_df["1시간당 배출량(g)"].round(1)
    st.dataframe(display_df.style.background_gradient(subset=["1km당 CO2 배출량(g)"], cmap="Greens"), use_container_width=True)
    st.markdown("- **연간 탄소 허용량 출처**: 녹색전환연구소 기준 (2030년 40% 감축 목표) 1인당 연간 온실가스 배출 예산 **5.9톤 (5,900 kg CO₂e)** 적용\n- **교통수단 배출량 출처**: 유럽환경청(EEA) 및 한국기후환경 네트워크 추정치 기반 예시 데이터")

st.caption("📱 모바일 최적화 대시보드 | 탄소여권 프로젝트")
