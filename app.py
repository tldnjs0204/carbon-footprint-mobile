import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 페이지 설정 - 모바일 세로 모드 최적화 (centered & sidebar 숨김)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="🌍 탄소배출 대시보드",
    page_icon="📱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# 2. CSS - 참고 사진 기반 딥 포레스트 그린 & 부드러운 파스텔 테마 (모바일 최적화)
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
    /* 모바일에서 카드 양옆 여백을 꽉 차게 조절 */
    .rounded-card {
        background: white;
        border-radius: 18px;
        padding: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        margin: 10px 0;
        border: 2px solid #A3C9AE;
    }
    .metric-card {
        background: linear-gradient(135deg, #34624C 0%, #A3C9AE 100%);
        border-radius: 18px;
        padding: 18px;
        color: white;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 4px 10px rgba(52, 98, 76, 0.15);
    }
    /* 모바일 화면에서 Streamlit 기본 상단 여백 줄이기 */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
    }
</style>
""", unsafe_allow_html=True)

# 제목
st.title("🌍 모바일 탄소 대시보드")
st.markdown("**📱 QR 스캔으로 접속하셨군요! 이동 습관을 간편하게 계산해보세요.**")
st.markdown("---")

# -----------------------------------------------------------------------------
# 3. 기초 데이터 및 탄소 예산 기준치 설정 (녹색전환연구소 기준 5.9톤)
# -----------------------------------------------------------------------------
ANNUAL_CARBON_BUDGET_KG = 5900.0

usage_data = {
    "자가용": 84.2,
    "항공기": 9.6,
    "버스": 3.9,
    "철도": 3.7,
}

emission_factor = {
    "자가용": 150,
    "버스": 28,
    "철도": 14,
    "항공기": 255,
}

avg_speed = {
    "자가용": 35,
    "버스": 20,
    "철도": 200,
    "항공기": 600,
}

# 1분당 배출량(g) = (평균속도 / 60) * 배출계수
hourly_emission = {mode: (avg_speed[mode] * emission_factor[mode] / 1000) for mode in usage_data}

# -----------------------------------------------------------------------------
# 4. 이동시간 선택 (모바일 터치 최적화 슬라이더)
# -----------------------------------------------------------------------------
st.header("⏱️ 이동 시간 선택")
st.caption("손가락으로 쉽게 바를 움직여서 시간을 맞춰보세요. (최대 6시간)")
travel_time_min = st.slider("1회 이동 시간 (분):", 10, 360, 60, step=10, label_visibility="collapsed")

hours_display = travel_time_min / 60
travel_time_hour = travel_time_min / 60
emission_by_time = {mode: (hourly_emission[mode] * travel_time_hour) for mode in usage_data}

# 모바일 화면이 좁으므로 메트릭 카드를 1개로 통합하여 깔끔하게 표시
st.markdown(f"""
<div class="metric-card">
    <h3 style="margin: 0; font-size: 1rem; opacity: 0.9;">선택하신 이동 시간</h3>
    <p style="margin: 5px 0; font-size: 2.2rem; font-weight: bold;">{travel_time_min}분 <span style="font-size: 1.3rem; font-weight: normal;">({hours_display:.1f}시간)</span></p>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. 수단별 배출량 (모바일 전용 세로 1줄 배치)
# -----------------------------------------------------------------------------
st.markdown("### 📋 수단별 배출량 비교")
st.caption("위아래로 스크롤하여 각 교통수단의 배출량을 확인하세요.")

# 모바일에서 글자가 깨지지 않도록 2칸 나누지 않고 1칸씩 세로로 층층이 쌓음!
st.markdown(f"""
<div class="rounded-card" style="border-left: 6px solid #E0E8A5;">
    <h3 style="color: #6A7525; margin: 0 0 5px 0;">🚗 자가용 (기준)</h3>
    <p style="font-size: 1.8rem; color: #8A9A28; font-weight: bold; margin: 0;">{emission_by_time['자가용']:.2f} <span style="font-size: 1rem; color: #666;">kg CO₂</span></p>
</div>

<div class="rounded-card" style="border-left: 6px solid #A3C9AE;">
    <h3 style="color: #34624C; margin: 0 0 5px 0;">🚌 버스</h3>
    <p style="font-size: 1.8rem; color: #34624C; font-weight: bold; margin: 0;">{emission_by_time['버스']:.2f} <span style="font-size: 1rem; color: #666;">kg CO₂</span></p>
    <p style="color: #34624C; font-size: 0.9rem; margin: 5px 0 0 0; font-weight: bold;">🎉 자가용 대비 {(1 - emission_by_time['버스']/emission_by_time['자가용'])*100:.0f}% 절감!</p>
</div>

<div class="rounded-card" style="border-left: 6px solid #34624C;">
    <h3 style="color: #34624C; margin: 0 0 5px 0;">🚄 고속열차 (KTX/SRT)</h3>
    <p style="font-size: 1.8rem; color: #34624C; font-weight: bold; margin: 0;">{emission_by_time['철도']:.2f} <span style="font-size: 1rem; color: #666;">kg CO₂</span></p>
    <p style="color: #34624C; font-size: 0.9rem; margin: 5px 0 0 0; font-weight: bold;">🎉 자가용 대비 {(1 - emission_by_time['철도']/emission_by_time['자가용'])*100:.0f}% 절감!</p>
</div>

<div class="rounded-card" style="border-left: 6px solid #F2C4B1;">
    <h3 style="color: #C85A32; margin: 0 0 5px 0;">✈️ 항공기</h3>
    <p style="font-size: 1.8rem; color: #D86A42; font-weight: bold; margin: 0;">{emission_by_time['항공기']:.2f} <span style="font-size: 1rem; color: #666;">kg CO₂</span></p>
    <p style="color: #C85A32; font-size: 0.9rem; margin: 5px 0 0 0;">⚠️ 가장 높은 배출량</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. 모바일 폭에 맞춘 콤팩트 막대 차트 (참고 사진 팔레트)
# -----------------------------------------------------------------------------
fig_bar = go.Figure(data=[
    go.Bar(
        x=list(emission_by_time.keys()),
        y=list(emission_by_time.values()),
        marker_color=['#E0E8A5', '#F2C4B1', '#A3C9AE', '#34624C'],
        text=[f"{v:.1f} kg" for v in emission_by_time.values()],
        textposition='auto',
        marker_line_color='white',
        marker_line_width=2
    )
])
fig_bar.update_layout(
    title="<b>📊 한눈에 비교하는 막대 그래프</b>",
    height=280,
    showlegend=False,
    yaxis_title="CO2 (kg)",
    plot_bgcolor='rgba(240,250,240,0.3)',
    paper_bgcolor='white',
    margin=dict(l=0, r=0, t=40, b=0)
)
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 7. 1.5도씨 연간 탄소 예산 원형 그래프 (참고 사진 테마 색상)
# -----------------------------------------------------------------------------
st.header("🌱 내 연간 탄소 예산")
st.markdown(f"**녹색전환연구소 2030 목표 기준:** 1인당 연간 허용량 **{ANNUAL_CARBON_BUDGET_KG/1000:.1f}톤**")

trip_emission_tons = emission_by_time['자가용'] / 1000
trip_usage_pct = (trip_emission_tons / (ANNUAL_CARBON_BUDGET_KG/1000)) * 100
trip_remaining_pct = 100 - trip_usage_pct

fig_pie_trip = go.Figure(data=[go.Pie(
    labels=["이번 이동 배출량", "연간 남은 허용량"],
    values=[trip_usage_pct, max(trip_remaining_pct, 0)],
    marker=dict(colors=['#F2C4B1', '#34624C'], line=dict(color='white', width=2)),
    textinfo='label+percent',
    textposition='auto',
    hovertemplate='<b>%{label}</b><br>%{value:.1f}%<extra></extra>'
)])
fig_pie_trip.update_layout(
    title="<b>자가용 이동 시 연간 예산 소진율</b>",
    height=280,
    margin=dict(l=0, r=0, t=30, b=0),
    paper_bgcolor='white',
    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
)
st.plotly_chart(fig_pie_trip, use_container_width=True)

# -----------------------------------------------------------------------------
# 8. 모바일 전용 아코디언 메뉴 (공유 및 참고문헌)
# -----------------------------------------------------------------------------
with st.expander("💡 1.5도씨 라이프스타일이란? (터치해서 열기)"):
    st.info(f"**1.5도씨 라이프스타일**은 기후위기 방지를 위해 1인당 연간 탄소배출량을 **{ANNUAL_CARBON_BUDGET_KG/1000:.1f}톤**으로 제한하는 캠페인입니다.\n\n현재 한국인 평균 배출량(약 12~13톤)의 절반 이하로 줄여야 합니다.")

with st.expander("🔗 친구에게 이 대시보드 공유하기"):
    st.write("화면 상단의 주소(URL)를 복사하거나 QR 코드를 캡처해서 공유해보세요!")

st.markdown("---")
st.caption("📱 모바일 최적화 대시보드 | 탄소여권 프로젝트")
