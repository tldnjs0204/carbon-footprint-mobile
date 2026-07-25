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
    .block-container { padding-top: 2rem !important; }
    .section-title { font-size: 1.1rem; font-weight: 700; color: #34624C; margin-top: 1.5rem; }
    .note { font-size: 0.78rem; color: #888; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

ANNUAL_BUDGET_KG = 5900.0

df = pd.DataFrame({
    "교통수단": ["KTX (장거리)", "고속버스 (장거리)", "자가용 (장거리)", "국내선 항공"],
    "1시간 배출량(kg)": [3.2, 2.5, 17.1, None],
    "점수/시간": [3, 3, 17, None],
    "카테고리": ["저탄소", "저탄소", "고탄소", "항공"]
})

st.title("🌿 탄소여권")
st.markdown("나의 여행 탄소발자국을 기록하고 연간 탄소예산 사용률을 확인하세요.")
st.caption("연간 예산 기준: 녹색전환연구소 1.5°C 라이프스타일 계산기 | 5,900kgCO₂e (2030년 목표)")
st.markdown("---")

# ══════════════════════════════════════════════
# PART 1. 장거리 이동 계산기
# ══════════════════════════════════════════════
st.markdown('<p class="section-title">🚄 PART 1. 장거리 이동 탄소 계산</p>', unsafe_allow_html=True)
st.markdown('<p class="note">수첩 p.8-9 장거리 이동 기록면과 함께 사용하세요.</p>', unsafe_allow_html=True)

selected_long = st.selectbox(
    "교통수단 선택",
    ["KTX (장거리)", "고속버스 (장거리)", "자가용 (장거리)", "국내선 항공"]
)

if selected_long == "국내선 항공":
    flight_routes = {
        "서울 ↔ 제주 편도": 100,
        "서울 ↔ 제주 왕복": 200,
        "부산 ↔ 제주 편도": 60,
        "부산 ↔ 제주 왕복": 120,
    }
    flight_route = st.selectbox("구간 선택", list(flight_routes.keys()))
    long_score = flight_routes[flight_route]
    st.info(f"✈ {flight_route} → **{long_score}점 ({long_score}kgCO₂e)**")
else:
    long_time = st.slider("소요시간 (시간)", 0.5, 8.0, 2.5, step=0.5)
    direction = st.radio("편도 / 왕복", ["편도", "왕복"], horizontal=True)
    multiplier = 1 if direction == "편도" else 2

    row = df[df["교통수단"] == selected_long].iloc[0]
    long_score = round(row["점수/시간"] * long_time * multiplier, 1)
    long_kg = round(row["1시간 배출량(kg)"] * long_time * multiplier, 1)

    car_score = round(17 * long_time * multiplier, 1)
    saved = round(car_score - long_score, 1)

    col1, col2, col3 = st.columns(3)
    col1.metric("이동 점수", f"{long_score}점")
    col2.metric("탄소배출량", f"{long_kg}kg")
    col3.metric("자가용 대비 절감", f"{saved}점" if saved >= 0 else "—")

    compare_df = pd.DataFrame([
        {"교통수단": "KTX", "점수": round(3 * long_time * multiplier, 1), "구분": "저탄소"},
        {"교통수단": "고속버스", "점수": round(3 * long_time * multiplier, 1), "구분": "저탄소"},
        {"교통수단": "자가용", "점수": round(17 * long_time * multiplier, 1), "구분": "고탄소"},
    ])
    fig = px.bar(
        compare_df, x="점수", y="교통수단", orientation="h",
        color="구분",
        color_discrete_map={"저탄소": "#52B788", "고탄소": "#E74C3C"},
        text="점수"
    )
    fig.update_layout(
        showlegend=False, height=180,
        margin=dict(l=0, r=10, t=10, b=10),
        xaxis_title="탄소여권 점수", yaxis_title=""
    )
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

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

total_score = long_score + daily_total
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
    <div style="font-size:0.8rem; color:#888; margin-top:6px">잔여 예산: {remaining_kg:,}kg</div>
</div>
""", unsafe_allow_html=True)

fig_donut = go.Figure(go.Pie(
    values=[total_kg, remaining_kg],
    labels=["이번 여행", "잔여 예산"],
    hole=0.6,
    marker_colors=["#52B788", "#D8F3DC"],
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
st.plotly_chart(fig_donut, use_container_width=True)

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
st.caption("🌿 탄소여권 프로젝트 | 제비여행 × 이매진피스\n연간 예산 기준: 녹색전환연구소 1.5°C 라이프스타일 계산기 (15lifestyle.or.kr)")
