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

# ══════════════════════════════════════════════
# 장거리 이동 배출계수 — 2026-09-09 확정값으로 교체
# (탄소여권_최종수치_마스터표.md §3, 탄소여권_웹앱_반영스펙.md §2 기준)
#
# ✅ 확인 출처가 있는 값: KTX·국내선항공·고속버스·도시내 대중교통·자가용(ITF)
# 🟡 잠정치(공식 출처 미확인, 인쇄물 반영 전 재확인 필요):
#     - 일반기차 평균속도 80km/h (경부선 서울-부산 약 5시간30분 소요 비공식 블로그
#       기준 역산치. 코레일 공식 시간표로 재확인 권장)
#     - 자가용(전기·내연기관) 고속도로 90km/h (정속 100km/h에서 정체 감안해 하향,
#       시원님 잠정 승인)
#     - 국제선 항공 평균 속도 800km/h (이착륙 포함 평균 순항속도 추정치, ICAO
#       계수 자체와는 무관 — 시간→거리 환산용으로만 사용)
# ══════════════════════════════════════════════
TRANSPORT = [
    # name,                                  g/km,   km/h,  category,   source
    ("지하철 / 전기열차",                     52,     33.0,  "대중교통", "ITF(1.5°C 라이프스타일 가이드북 수록, 녹색전환연구소) · 속도: 서울교통공사 2024 표정속도"),
    ("시내버스",                              62,     17.1,  "대중교통", "ITF(1.5°C 라이프스타일 가이드북 수록, 녹색전환연구소) · 속도: TOPIS 2025 서울시 버스 평균"),
    ("고속열차 (KTX/SRT)",                    21.9,   173,   "대중교통", "한국철도공사 2022 환경경영보고서 p.13, 환경부 탄소성적표지 인증"),
    ("일반기차 (무궁화·새마을)",               35.46,  80,    "대중교통", "DEFRA/DESNZ 2025 National rail 🟡 속도 잠정치"),
    ("고속/시외버스",                         27.76,  95,    "대중교통", "DEFRA/DESNZ 2025 Coach"),
    ("전기 승용차 (BEV)",                     125,    90,    "개인교통", "ITF(1.5°C 라이프스타일 가이드북 수록) 🟡 속도 잠정치"),
    ("자가용 (가솔린·디젤·하이브리드)",        161,    90,    "개인교통", "ITF(1.5°C 라이프스타일 가이드북 수록, 내연기관 승용차) 🟡 속도 잠정치"),
    ("국내선 항공기",                         124.2,  450,   "항공",     "ICAO ICEC 직접 조회, 김포-제주"),
    ("국제선 항공기 (이코노미)",               53.3,   800,   "항공",     "ICAO ICEC 4개 노선 평균(방콕·발리·프랑크푸르트·뉴욕) 🟡 속도 잠정치"),
    ("국제선 항공기 (비즈니스)",               191.9,  800,   "항공",     "이코노미 × 약 3.6배(ICAO ICEC 좌석등급 비교) 🟡 속도 잠정치"),
]

df_all = pd.DataFrame(TRANSPORT, columns=["교통수단", "1km당 CO2 배출량(g)", "평균시속(km/h)", "카테고리", "출처"])
df_all["1시간당 배출량(g)"] = df_all["평균시속(km/h)"] * df_all["1km당 CO2 배출량(g)"]

# 하드코딩 없이 계수표에서 그대로 파생 (기존 버그: 점수 카드와 비교그래프 값이 어긋났음 — 수정 완료)
transport_score_map = dict(zip(df_all["교통수단"], df_all["1시간당 배출량(g)"] / 1000))

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
st.markdown('<p class="note">수첩 p.15-16 장거리 이동 기록면과 함께 사용하세요.</p>', unsafe_allow_html=True)
st.caption("⚠️ 일반기차·국제선 항공·자가용의 평균 속도는 공식 출처 확인 전 잠정치입니다. 배출계수 자체는 확정값입니다.")

selected_transport = st.selectbox(
    "1️⃣ 이용할 교통수단 선택:",
    df_all["교통수단"].tolist(),
    index=2
)

time_hours = st.slider("2️⃣ 1회 이동 시간 (시간):", 0.5, 6.0, 2.5, step=0.5)
direction = st.radio("3️⃣ 편도 / 왕복", ["편도", "왕복"], horizontal=True)
multiplier = 1 if direction == "편도" else 2

selected_speed = df_all.loc[df_all["교통수단"] == selected_transport, "평균시속(km/h)"].iloc[0]
# 이번 이동 거리(사용자가 고른 수단·시간 기준) — 아래 "전체 수단 비교"를 같은 거리로 비교하는 데 사용
trip_distance_km = round(selected_speed * time_hours * multiplier, 1)

score_per_hour = transport_score_map[selected_transport]
long_kg = round(score_per_hour * time_hours * multiplier, 2)
long_score = long_kg

st.subheader(f"📊 '{selected_transport}' 결과")
col1, col2 = st.columns(2)
col1.metric("탄소여권 점수", f"{long_score}점")
col2.metric("탄소배출량", f"{long_kg}kg CO₂")

st.markdown("---")

# 전체 수단 비교 — ✅ 같은 거리(trip_distance_km) 기준으로 비교
# (마스터표 §3 지적사항 반영: 시간 기준 비교는 KTX·고속버스 순위가 실제 구간 기준과
#  반대로 뒤집히는 문제가 있었음. 이제 "이번 이동과 같은 거리"를 갔다면 수단별로
#  얼마나 배출하는지 비교한다.)
st.subheader(f"💡 이번 이동 거리(약 {trip_distance_km:g}km)를 다른 수단으로 갔다면?")
df_all["비교배출량(g)"] = df_all["1km당 CO2 배출량(g)"] * trip_distance_km

# 배출량 큰 것부터 위에서 아래로 나오도록 순서를 직접 지정
# (color로 묶으면 정렬한 데이터프레임 순서가 그대로 안 먹히는 경우가 있어
#  category_orders로 명시적으로 y축 순서를 고정)
order_desc = df_all.sort_values("비교배출량(g)", ascending=False)["교통수단"].tolist()

fig_bar = px.bar(
    df_all,
    x="비교배출량(g)", y="교통수단",
    color="카테고리",
    color_discrete_map=COLOR_MAP,
    orientation="h",
    category_orders={"교통수단": order_desc}
)
fig_bar.update_layout(
    height=380,
    margin=dict(l=0, r=20, t=10, b=10),
    xaxis_title="비교배출량(g)", yaxis_title=""
)
st.plotly_chart(fig_bar, use_container_width=True)

# 감축 효과 — 같은 거리 기준으로 KTX 전환 시 절감량 계산
st.subheader("🌱 전환 시 감축 효과")
train_g_km = df_all.loc[df_all["교통수단"] == "고속열차 (KTX/SRT)", "1km당 CO2 배출량(g)"].iloc[0]
train_kg = round(train_g_km * trip_distance_km / 1000, 2)
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
    textinfo="percent"  # ← "label+percent"에서 변경, 레이블 제거
))
fig_donut.update_layout(
    height=260,
    margin=dict(l=0, r=0, t=20, b=0),
    showlegend=True,  # ← 레전드로 대신 표시
    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
    annotations=[dict(
        text=f"{budget_pct}%",
        x=0.5, y=0.5,
        font_size=26, font_color="#34624C",
        showarrow=False
    )]
)
st.plotly_chart(fig_donut, use_container_width=True)

with st.expander("📎 배출계수 출처 보기"):
    st.dataframe(
        df_all[["교통수단", "1km당 CO2 배출량(g)", "평균시속(km/h)", "출처"]],
        use_container_width=True, hide_index=True
    )

st.markdown("---")
st.caption(
    "📱 탄소여권 프로젝트 | 제비여행 × 이매진피스\n\n"
    "연간 예산 기준: 녹색전환연구소 1.5°C 라이프스타일 계산기 (15lifestyle.or.kr)\n\n"
    "장거리 이동 배출계수 출처: 한국철도공사 2022 환경경영보고서·환경부 탄소성적표지(KTX) · "
    "ICAO ICEC(항공) · DEFRA/DESNZ 2025(고속버스·일반기차) · "
    "ITF, 1.5°C 라이프스타일 가이드북·녹색전환연구소(도시내 대중교통·자가용)\n\n"
    "⚠️ 일반기차·국제선 항공·자가용(장거리)의 평균 속도 가정은 공식 출처 확인 전 잠정치입니다."
)
