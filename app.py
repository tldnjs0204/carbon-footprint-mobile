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
# ✅ 확인 출처가 있는 값: KTX·국내선항공·고속버스·자가용(ITF)
# 🟡 잠정치(공식 출처 미확인, 인쇄물 반영 전 재확인 필요):
#     - 일반기차 평균속도 80km/h (경부선 서울-부산 약 5시간30분 소요 비공식 블로그
#       기준 역산치. 코레일 공식 시간표로 재확인 권장)
#     - 자가용(전기·내연기관) 고속도로 90km/h (정속 100km/h에서 정체 감안해 하향,
#       시원님 잠정 승인)
#     - 여객선(페리) 평균속도 19km/h (목포-제주 노선 85km ÷ 4시간30분 역산치,
#       Direct Ferries 조회. 단일 노선 기준이라 다른 항로와 다를 수 있음)
#
# 국제선 항공은 2026-09-09 시원님 결정으로 선택지에서 제거함(속도 가정 800km/h가
# 미확인 잠정치였던 것도 이유 중 하나). 필요해지면 이 파일 히스토리에서 복원 가능.
#
# 여객선(페리)은 2026-09-09 추가함 — 목포-제주처럼 항공과 비교되는 항로가 있어서
# "전체 수단 비교" 그래프에서 항공 대안으로 볼 수 있게 함. 배출계수는
# DEFRA/DESNZ 2025 Ferry(car passenger) 확정 자료(129.33g/km) — 국내 카페리는
# 승객 상당수가 차를 싣고 타는 경우가 많아 "도보 승객"(18.71g/km)보다 이 기준이
# 더 현실적이라고 판단해 2026-09-09 변경. 속도는 목포-제주 1개 노선만 역산한 값이라
# 다른 항로(완도-제주, 여수-제주 등)에는 안 맞을 수 있음.
#
# 지하철·시내버스는 2026-09-09 선택지에서 제거함 — PART1은 장거리 이동 계산용인데
# 도시 내 이동 수단이라 맞지 않음(시원님 결정). KTX 비교 기준(LOW_CARBON)도
# 이에 맞춰 KTX만 남김.
# ══════════════════════════════════════════════
TRANSPORT = [
    # name,                                  g/km,   km/h,  category,   source
    ("고속열차 (KTX/SRT)",                    21.9,   173,   "대중교통", "한국철도공사 2022 환경경영보고서 p.13, 환경부 탄소성적표지 인증"),
    ("일반기차 (무궁화·새마을)",               35.46,  80,    "대중교통", "DEFRA/DESNZ 2025 National rail 🟡 속도 잠정치"),
    ("고속/시외버스",                         27.76,  95,    "대중교통", "DEFRA/DESNZ 2025 Coach"),
    ("여객선 (페리)",                          129.33, 19,    "선박",     "DEFRA/DESNZ 2025 Ferry(car passenger) · 속도: 목포-제주 노선(약 85km/4시간30분, Direct Ferries) 🟡 단일 노선 기준 잠정치"),
    ("전기 승용차 (BEV)",                     125,    90,    "개인교통", "ITF(1.5°C 라이프스타일 가이드북 수록) 🟡 속도 잠정치"),
    ("자가용 (가솔린·디젤·하이브리드)",        161,    90,    "개인교통", "ITF(1.5°C 라이프스타일 가이드북 수록, 내연기관 승용차) 🟡 속도 잠정치"),
    ("국내선 항공기 (이코노미)",               130.9,  450,   "항공",     "ICAO ICEC 국내 4개 노선 직접 조회 · 거리별로 다름(아래 로직 참고)"),
    ("국내선 항공기 (비즈니스)",               261.8,  450,   "항공",     "국내선 이코노미 × 약 2.0배(ICAO ICEC 국내 노선 좌석등급 비교)"),
]

df_all = pd.DataFrame(TRANSPORT, columns=["교통수단", "1km당 CO2 배출량(g)", "평균시속(km/h)", "카테고리", "출처"])
df_all["1시간당 배출량(g)"] = df_all["평균시속(km/h)"] * df_all["1km당 CO2 배출량(g)"]

# 하드코딩 없이 계수표에서 그대로 파생 (기존 버그: 점수 카드와 비교그래프 값이 어긋났음 — 수정 완료)
transport_score_map = dict(zip(df_all["교통수단"], df_all["1시간당 배출량(g)"] / 1000))

# KTX보다 배출량이 같거나 낮은 수단 → "최고의 선택" 표시
# (지하철·시내버스는 2026-09-09 선택지에서 제거되어 KTX만 남음)
LOW_CARBON = {"고속열차 (KTX/SRT)"}

COLOR_MAP = {
    "대중교통": "#34624C",
    "개인교통": "#E0E8A5",
    "항공":     "#F2C4B1",
    "선박":     "#5FA9A4"
}

# 실제 운항 중인 국내선 중 가장 짧은 노선은 광주-제주(약 182~186km, ICAO ICEC 실측·나무위키 교차확인).
# 그보다 짧은 거리에서는 존재하지 않는 항공 노선이므로 보수적으로 180km를 하한선으로 둔다.
# (2026-09-09, 시원님 확인 후 반영)
MIN_FLIGHT_DISTANCE_KM = 180
FLIGHT_TRANSPORTS = set(df_all.loc[df_all["카테고리"] == "항공", "교통수단"])

st.title("🌍 여행 탄소발자국 대시보드")
st.markdown("---")

# ══════════════════════════════════════════════
# PART 1. 장거리 이동 탄소 계산
# ══════════════════════════════════════════════
st.markdown('<p class="section-title">🚄 PART 1. 장거리 이동 탄소 계산</p>', unsafe_allow_html=True)
st.markdown('<p class="note">수첩 p.15-16 장거리 이동 기록면과 함께 사용하세요.</p>', unsafe_allow_html=True)
st.caption("⚠️ 일반기차·자가용·여객선(페리)의 평균 속도는 공식 출처 확인 전 잠정치입니다. 배출계수 자체는 확정값입니다.")
st.caption("✈️ 국내선 항공은 이동 거리(300km 기준)에 따라 배출계수가 자동으로 달라집니다 — 단거리일수록 이착륙 고정 배출 비중이 커져 g/km가 높습니다.")

selected_transport = st.selectbox(
    "1️⃣ 이용할 교통수단 선택:",
    df_all["교통수단"].tolist(),
    index=0
)

time_hours = st.slider("2️⃣ 1회 이동 시간 (시간):", 0.5, 6.0, 2.5, step=0.5)
direction = st.radio("3️⃣ 편도 / 왕복", ["편도", "왕복"], horizontal=True)
multiplier = 1 if direction == "편도" else 2

selected_speed = df_all.loc[df_all["교통수단"] == selected_transport, "평균시속(km/h)"].iloc[0]
# 이번 이동 거리(사용자가 고른 수단·시간 기준) — 아래 "전체 수단 비교"를 같은 거리로 비교하는 데 사용
trip_distance_km = round(selected_speed * time_hours * multiplier, 1)

# ══════════════════════════════════════════════
# 국내선 항공 — 거리별 배출계수 재적용 (2026-09-09, ICAO ICEC 국내 4개 노선 직접 조회)
#   광주(KWJ)-제주(CJU) 182km 181.3g/km, 포항(KPO)-김포(GMP) 291km 147.8g/km
#     → 평균 164.6g/km (<300km 구간)
#   김포(GMP)-부산(PUS) 327km 137.6g/km, 김포(GMP)-제주(CJU) 451km 124.2g/km
#     → 평균 130.9g/km (300~500km 구간)
#   비즈니스는 3개 노선 좌석등급 비율 평균 약 2.0배 (국제선 3.6배와는 다른 국내 전용 값)
# 짧은 구간일수록 이착륙(LTO) 고정 배출이 차지하는 비중이 커져 g/km가 높아짐 — 실측 기반.
# ══════════════════════════════════════════════
DOMESTIC_FLIGHT_ECONOMY_SHORT = 164.6  # <300km
DOMESTIC_FLIGHT_ECONOMY_LONG = 130.9   # 300~500km
DOMESTIC_BUSINESS_RATIO = 2.0

domestic_eco_g_km = DOMESTIC_FLIGHT_ECONOMY_SHORT if trip_distance_km < 300 else DOMESTIC_FLIGHT_ECONOMY_LONG
domestic_biz_g_km = round(domestic_eco_g_km * DOMESTIC_BUSINESS_RATIO, 1)

df_all.loc[df_all["교통수단"] == "국내선 항공기 (이코노미)", "1km당 CO2 배출량(g)"] = domestic_eco_g_km
df_all.loc[df_all["교통수단"] == "국내선 항공기 (비즈니스)", "1km당 CO2 배출량(g)"] = domestic_biz_g_km
df_all["1시간당 배출량(g)"] = df_all["평균시속(km/h)"] * df_all["1km당 CO2 배출량(g)"]
transport_score_map = dict(zip(df_all["교통수단"], df_all["1시간당 배출량(g)"] / 1000))

# 선택한 수단이 항공인데, 계산된 거리가 실제 존재하는 최단 국내선 노선보다도 짧으면
# 존재하지 않는 시나리오이므로 계산을 막고 안내만 표시한다.
if selected_transport in FLIGHT_TRANSPORTS and trip_distance_km < MIN_FLIGHT_DISTANCE_KM:
    st.error(
        f"⚠️ 이 조건(약 {trip_distance_km:g}km)으로는 실제 운항하는 항공 노선이 없습니다. "
        f"국내선 최단 노선인 광주-제주도 약 182~186km입니다. "
        f"이동 시간을 늘리거나 다른 교통수단을 선택해주세요."
    )
    st.stop()

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
st.caption(
    "⚠️ 자가용은 대부분 자기 소유 차량을 쓴다는 특성 때문에 제조·발전믹스까지 포함한 "
    "생애주기(전 과정) 기준으로 측정되고, 항공·KTX 등은 이미 존재하는 교통수단을 "
    "이용만 하는 것이라 운행 단계(연료 연소)만 측정됩니다. 그래서 이 그래프에서 자가용이 "
    "항공과 비슷하거나 더 높게 보이더라도, 서로 다른 산정 기준을 비교하고 있다는 점을 "
    "감안해서 봐주세요."
)
df_all["비교배출량(g)"] = df_all["1km당 CO2 배출량(g)"] * trip_distance_km

# 이 거리보다 짧은 국내선·국제선 항공 노선은 실제로 존재하지 않으므로,
# 비교그래프에서도 항공 항목 전체를 제외한다 (2026-09-09 반영).
if trip_distance_km < MIN_FLIGHT_DISTANCE_KM:
    df_cmp = df_all[df_all["카테고리"] != "항공"].copy()
    st.caption(
        f"✈️ 이 거리(약 {trip_distance_km:g}km)보다 짧은 항공 노선은 실제로 없어 "
        f"비교그래프에서 항공 수단을 제외했습니다."
    )
else:
    df_cmp = df_all.copy()

# 배출량 큰 것부터 위에서 아래로 나오도록 순서를 직접 지정
# (color로 묶으면 정렬한 데이터프레임 순서가 그대로 안 먹히는 경우가 있어
#  category_orders로 명시적으로 y축 순서를 고정)
order_desc = df_cmp.sort_values("비교배출량(g)", ascending=False)["교통수단"].tolist()

fig_bar = px.bar(
    df_cmp,
    x="비교배출량(g)", y="교통수단",
    color="카테고리",
    color_discrete_map=COLOR_MAP,
    orientation="h",
    category_orders={"교통수단": order_desc}
)
fig_bar.update_layout(
    height=440,
    margin=dict(l=10, r=10, t=10, b=70),
    xaxis_title="비교배출량(g)", yaxis_title="",
    legend_title_text="",
    legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5)
)
st.plotly_chart(fig_bar, use_container_width=True)

# 감축 효과 — 같은 거리 기준으로 KTX 전환 시 절감량 계산
st.subheader("🌱 전환 시 감축 효과")
train_g_km = df_all.loc[df_all["교통수단"] == "고속열차 (KTX/SRT)", "1km당 CO2 배출량(g)"].iloc[0]
train_kg = round(train_g_km * trip_distance_km / 1000, 2)
reduction_kg = round(long_kg - train_kg, 2)

if selected_transport in LOW_CARBON:
    # KTX: 최고의 선택
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
    "ICAO ICEC(국내선 항공, 광주-제주·포항-김포·김포-부산·김포-제주 4개 노선 직접 조회) · "
    "DEFRA/DESNZ 2025(고속버스·일반기차·여객선) · "
    "ITF, 1.5°C 라이프스타일 가이드북·녹색전환연구소(자가용)"
)
