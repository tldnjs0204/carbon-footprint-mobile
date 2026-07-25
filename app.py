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

# ══════════════════════════════════════════════
# PART 1. 장거리 이동 탄소 계산
# ══════════════════════════════════════════════
st.markdown('<p class="section-title">🚄 PART 1. 장거리 이동 탄소 계산</p>', unsafe_allow_html=True)
st.markdown('<p class="note">수첩 p.8-9 장거리 이동 기록면과 함께 사용하세요.</p>', unsafe_allow_html=True)

selected_transport = st.selectbox(
    "1️⃣ 이용할 교통수단 선택:",
    df_all["교통수단"].tolist(),
    index=1
)

time_hours = st.slider("2️⃣ 1회 이동 시간 (시간):", 0.5, 6.0, 2.5, step=0.5)
direction = st.radio("3️⃣ 편도 / 왕복", ["편도", "왕복"], horizontal=True)
multiplier = 1 if direction == "편도" else 2

score_per_hour = transport_score_map[selected_transport]
long_kg = round(score_per_hour * time_hours * multiplier, 2)
long_score = long_kg

car_kg = round(CAR_SCORE_PER_HOUR * time_hours * multiplier, 2)
saved = round(car_kg - long_kg, 2)

st.subheader(f"📊 '{selected_transport}' 결과")
col1, col2, col3 = st.columns(3)
col1.metric("탄소여권 점수", f"{long_score}점")
col2.metric("탄소배출량", f"{long_kg}kg CO₂")
col3.metric("가솔린 승용차 대비 절감",
            f"{saved}점" if saved > 0 else "기준 수단")

st.markdown("---")

# 전체 수단 비교
st.subheader("💡 동일 시간 이동 시 전체 수단 비교")
df_all["비교배출량(g)"] = df_all["1시간당 배출량(g)"] * time_hours
fig_bar = px.bar(
    df_all.sort_values("비교배출량(g)"),
    x="비교배출량(g)", y="교통수단",
    color="카테고리",
    color_discrete_map=COLOR_MAP,
    orientation="h"
)
fig_bar.update_layout(
    height=350,
    margin=dict(l=0, r=20, t=10, b=10),
    xaxis_title="비교배출량(g)", yaxis_title=""
)
st.plotly_chart(fig_bar, use_container_width=True)

# 감축 효과 — 수정된 로직
st.subheader("🌱 전환 시 감축 효과")
train_score_per_hour = transport_score_map["고속열차 (KTX/SRT)"]
train_kg = round(train_score_per_hour * time_hours * multiplier, 2)
reduction_kg = round(long_kg - train_kg, 2)

if selected_transport in LOW_CARBON:
    # KTX·지하철·시내버스: 최고의 선택
    st.markdown("""
    <div style="background:#F8FCF8; border:2px solid #A3C9AE;
         padding:20px; border-radius:18px; text-align:center">
        🎉 지구를 살리는 최고의 선택입니다!
    </div>""", unsafe_allow_html=True)
elif reduction_kg > 0:
    # 고배출 수단: KTX 전환 시 감축량 표시
    st.success(
        f"🎉 동일 거리를 **고속열차(KTX/SRT)**로 전환 시, "
        f"**{reduction_kg:.2f} kg CO₂**를 줄일 수 있습니다!\n\n"
        f"(연간 탄소 예산의 **{(reduction_kg / ANNUAL_BUDGET_KG)*100:.2f}%** 절약)"
    )
    compare_df = pd.DataFrame({
        "구분": ["현재", "전환(KTX)"],
        "배출량(kg)": [long_kg, train_kg]
    })
    st.plotly_chart(
        px.pie(compare_df, names="구분", values="배출량(kg)",
               color_discrete_sequence=["#F2C4B1", "#A3C9AE"], hole=0.4),
        use_container_width=True
    )
else:
    # 고속버스처럼 KTX와 비슷한 수준
    st.markdown("""
    <div style="background:#F8FCF8; border:2px solid #A3C9AE;
         padding:20px; border-radius:18px; text-align:center">
        👍 KTX와 비슷한 수준의 저탄소 이동입니다!
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ══════════════════════════════════════════════
# PART 2. 여행 탄소발자국 총점 입력
# ══════════════════════════════════════════════
st.markdown('<p class="section-title">📓 PART 2. 여행 탄소발자국 총점 입력</p>', unsafe_allow_html=True)
st.markdown('<p class="note">수첩 Day 1~5 기록면의 하루 총점을 모두 더한 값을 입력하세요.</p>', unsafe_allow_html=True)

daily_total = st.number_input(
    "여행 탄소발자국 점수 합계",
    min_value=0, max_value=500, value=50, step=1
)

st.markdown("---")

# ══════════════════════════════════════════════
# PART 3. 총결산 & 연간 예산 사용률
# ══════════════════════════════════════════════
st.markdown('<p class="section-title">🌍 PART 3. 이번 여행 총결산</p>', unsafe_allow_html=True)

total_score = round(long_score + daily_total, 2)
total_kg = total_score
budget_pct = round((total_kg / ANNUAL_BUDGET_KG) * 100, 2)
remaining_kg = max(0, ANNUAL_BUDGET_KG - total_kg)

st.markdown(f"""
<div class="result-box">
    <div style="font-size:0.95rem; opacity:0.85; margin-bottom:6px">이번 여행 탄소여권 총점</div>
    <div style="font-size:2.6rem; font-weight:900">{total_score}점</div>
    <div style="font-size:0.95rem; opacity:0.85; margin-top:4px">= {total_kg} kgCO₂e</div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
col1.metric("장거리 이동", f"{long_score}점")
col2.metric("도시 내 여행 합계", f"{daily_total}점")

st.markdown("---")
st.markdown("**1.5°C 라이프스타일 연간 탄소예산 사용률**")

st.markdown(f"""
<div class="rounded-card" style="text-align:center">
    <div style="font-size:0.85rem; color:#888">
        녹색전환연구소 2030년 목표 연간 5,900 kgCO₂e 중
    </div>
    <div style="font-size:2.4rem; font-weight:900; color:#34624C">{budget_pct}%</div>
    <div style="font-size:0.9rem; color:#555">사용 ({total_kg}kg / 5,900kg)</div>
    <div style="font-size:0.8rem; color:#888; margin-top:6px">잔여 예산: {remaining_kg:,.1f}kg</div>
</div>
""", unsafe_allow_html=True)

# ── 도넛 차트 (plotly_chart 호출 추가) ────────
fig_donut = go.Figure(go.Pie(
    values=[total_kg, remaining_kg],
    labels=["이번 여행", "잔여 예산"],
    hole=0.6,
    marker_colors=["#F2C4B1", "#34624C"],
    textinfo="label+percent"
))
fig_donut.update_layout(
    height=260,
    margin=dict(l=0, r=0, t=20, b=0),
    showlegend=False,
    annotations=[dict(
        text=f"{budget_pct}%",
        x=0.5, y=0.5,
        font_size=26, font_color="#34624C",
        showarrow=False
    )]
)
st.plotly_chart(fig_donut, use_container_width=True)  # ← 누락됐던 호출 복구

if budget_pct <= 2:
    msg, color = "🌿 매우 훌륭합니다! 연간 예산의 2% 이내로 여행했습니다.", "#34624C"
elif budget_pct <= 5:
    msg, color = "👍 양호한 수준입니다. 이동 수단 선택이 잘 됐네요.", "#52B788"
elif budget_pct <= 10:
    msg, color = "⚠️ 연간 예산의 10%를 이번 여행에 사용했습니다. 장거리 이동 수단을 바꾸면 크게 줄일 수 있습니다.", "#E67E22"
else:
    msg, color = "🔴 연간 예산의 10% 이상을 사용했습니다. 다음 여행에서는 기차·버스 선택을 고려해보세요.", "#E74C3C"

st.markdown(f"""
<div style="background:{color}15; border-left:4px solid {color};
     padding:12px 16px; border-radius:8px; margin-top:8px; font-size:0.9rem; color:#333">
{msg}
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.caption(
    "📱 탄소여권 프로젝트 | 제비여행 × 이매진피스\n"
    "연간 예산 기준: 녹색전환연구소 1.5°C 라이프스타일 계산기 (15lifestyle.or.kr)\n"
    "출처: KOTEMS · 환경부 · 한국철도공사 ESG · Cornell CHSB · Poore & Nemecek 2018 · ICAO"
)
