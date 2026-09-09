diff --git a/app.py b/app.py
index f616332..bd78008 100644
--- a/app.py
+++ b/app.py
@@ -36,35 +36,38 @@ st.markdown("""
 
 ANNUAL_BUDGET_KG = 5900.0
 
-data = {
-    "교통수단": [
-        "지하철 / 전기열차", "고속열차 (KTX/SRT)", "시내버스",
-        "고속/시외버스", "전기 승용차 (BEV)", "하이브리드 승용차",
-        "가솔린 승용차", "디젤 승용차", "국내선 항공기"
-    ],
-    "1km당 CO2 배출량(g)": [6, 14, 28, 33, 40, 90, 150, 170, 255],
-    "평균시속(km/h)": [40, 200, 20, 80, 35, 35, 35, 35, 600],
-    "카테고리": [
-        "대중교통", "대중교통", "대중교통", "대중교통",
-        "개인교통", "개인교통", "개인교통", "개인교통", "항공"
-    ]
-}
-df_all = pd.DataFrame(data)
-df_all["1시간당 배출량(g)"] = df_all["평균시속(km/h)"] * df_all["1km당 CO2 배출량(g)"]
+# ══════════════════════════════════════════════
+# 장거리 이동 배출계수 — 2026-09-09 확정값으로 교체
+# (탄소여권_최종수치_마스터표.md §3, 탄소여권_웹앱_반영스펙.md §2 기준)
+#
+# ✅ 확인 출처가 있는 값: KTX·국내선항공·고속버스·도시내 대중교통·자가용(ITF)
+# 🟡 잠정치(공식 출처 미확인, 인쇄물 반영 전 재확인 필요):
+#     - 일반기차 평균속도 80km/h (경부선 서울-부산 약 5시간30분 소요 비공식 블로그
+#       기준 역산치. 코레일 공식 시간표로 재확인 권장)
+#     - 자가용(전기·내연기관) 고속도로 90km/h (정속 100km/h에서 정체 감안해 하향,
+#       시원님 잠정 승인)
+#     - 국제선 항공 평균 속도 800km/h (이착륙 포함 평균 순항속도 추정치, ICAO
+#       계수 자체와는 무관 — 시간→거리 환산용으로만 사용)
+# ══════════════════════════════════════════════
+TRANSPORT = [
+    # name,                                  g/km,   km/h,  category,   source
+    ("지하철 / 전기열차",                     52,     33.0,  "대중교통", "ITF(1.5°C 라이프스타일 가이드북 수록, 녹색전환연구소) · 속도: 서울교통공사 2024 표정속도"),
+    ("시내버스",                              62,     17.1,  "대중교통", "ITF(1.5°C 라이프스타일 가이드북 수록, 녹색전환연구소) · 속도: TOPIS 2025 서울시 버스 평균"),
+    ("고속열차 (KTX/SRT)",                    21.9,   173,   "대중교통", "한국철도공사 2022 환경경영보고서 p.13, 환경부 탄소성적표지 인증"),
+    ("일반기차 (무궁화·새마을)",               35.46,  80,    "대중교통", "DEFRA/DESNZ 2025 National rail 🟡 속도 잠정치"),
+    ("고속/시외버스",                         27.76,  95,    "대중교통", "DEFRA/DESNZ 2025 Coach"),
+    ("전기 승용차 (BEV)",                     125,    90,    "개인교통", "ITF(1.5°C 라이프스타일 가이드북 수록) 🟡 속도 잠정치"),
+    ("자가용 (가솔린·디젤·하이브리드)",        161,    90,    "개인교통", "ITF(1.5°C 라이프스타일 가이드북 수록, 내연기관 승용차) 🟡 속도 잠정치"),
+    ("국내선 항공기",                         124.2,  450,   "항공",     "ICAO ICEC 직접 조회, 김포-제주"),
+    ("국제선 항공기 (이코노미)",               53.3,   800,   "항공",     "ICAO ICEC 4개 노선 평균(방콕·발리·프랑크푸르트·뉴욕) 🟡 속도 잠정치"),
+    ("국제선 항공기 (비즈니스)",               191.9,  800,   "항공",     "이코노미 × 약 3.6배(ICAO ICEC 좌석등급 비교) 🟡 속도 잠정치"),
+]
 
-transport_score_map = {
-    "지하철 / 전기열차":  40  * 6   / 1000,
-    "고속열차 (KTX/SRT)": 3.2,
-    "시내버스":            20  * 28  / 1000,
-    "고속/시외버스":       2.5,
-    "전기 승용차 (BEV)":  1.5,
-    "하이브리드 승용차":   35  * 90  / 1000,
-    "가솔린 승용차":       5.25,
-    "디젤 승용차":         5.95,
-    "국내선 항공기":       600 * 255 / 1000,
-}
+df_all = pd.DataFrame(TRANSPORT, columns=["교통수단", "1km당 CO2 배출량(g)", "평균시속(km/h)", "카테고리", "출처"])
+df_all["1시간당 배출량(g)"] = df_all["평균시속(km/h)"] * df_all["1km당 CO2 배출량(g)"]
 
-CAR_SCORE_PER_HOUR = transport_score_map["가솔린 승용차"]
+# 하드코딩 없이 계수표에서 그대로 파생 (기존 버그: 점수 카드와 비교그래프 값이 어긋났음 — 수정 완료)
+transport_score_map = dict(zip(df_all["교통수단"], df_all["1시간당 배출량(g)"] / 1000))
 
 # KTX보다 배출량이 같거나 낮은 수단 → "최고의 선택" 표시
 LOW_CARBON = {"지하철 / 전기열차", "시내버스", "고속열차 (KTX/SRT)"}
@@ -82,55 +85,65 @@ st.markdown("---")
 # PART 1. 장거리 이동 탄소 계산
 # ══════════════════════════════════════════════
 st.markdown('<p class="section-title">🚄 PART 1. 장거리 이동 탄소 계산</p>', unsafe_allow_html=True)
-st.markdown('<p class="note">수첩 p.8-9 장거리 이동 기록면과 함께 사용하세요.</p>', unsafe_allow_html=True)
+st.markdown('<p class="note">수첩 p.15-16 장거리 이동 기록면과 함께 사용하세요.</p>', unsafe_allow_html=True)
+st.caption("⚠️ 일반기차·국제선 항공·자가용의 평균 속도는 공식 출처 확인 전 잠정치입니다. 배출계수 자체는 확정값입니다.")
 
 selected_transport = st.selectbox(
     "1️⃣ 이용할 교통수단 선택:",
     df_all["교통수단"].tolist(),
-    index=1
+    index=2
 )
 
 time_hours = st.slider("2️⃣ 1회 이동 시간 (시간):", 0.5, 6.0, 2.5, step=0.5)
 direction = st.radio("3️⃣ 편도 / 왕복", ["편도", "왕복"], horizontal=True)
 multiplier = 1 if direction == "편도" else 2
 
+selected_speed = df_all.loc[df_all["교통수단"] == selected_transport, "평균시속(km/h)"].iloc[0]
+# 이번 이동 거리(사용자가 고른 수단·시간 기준) — 아래 "전체 수단 비교"를 같은 거리로 비교하는 데 사용
+trip_distance_km = round(selected_speed * time_hours * multiplier, 1)
+
 score_per_hour = transport_score_map[selected_transport]
 long_kg = round(score_per_hour * time_hours * multiplier, 2)
 long_score = long_kg
 
-car_kg = round(CAR_SCORE_PER_HOUR * time_hours * multiplier, 2)
-saved = round(car_kg - long_kg, 2)
-
 st.subheader(f"📊 '{selected_transport}' 결과")
-col1, col2, col3 = st.columns(3)
+col1, col2 = st.columns(2)
 col1.metric("탄소여권 점수", f"{long_score}점")
 col2.metric("탄소배출량", f"{long_kg}kg CO₂")
-col3.metric("가솔린 승용차 대비 절감",
-            f"{saved}점" if saved > 0 else "기준 수단")
 
 st.markdown("---")
 
-# 전체 수단 비교
-st.subheader("💡 동일 시간 이동 시 전체 수단 비교")
-df_all["비교배출량(g)"] = df_all["1시간당 배출량(g)"] * time_hours
+# 전체 수단 비교 — ✅ 같은 거리(trip_distance_km) 기준으로 비교
+# (마스터표 §3 지적사항 반영: 시간 기준 비교는 KTX·고속버스 순위가 실제 구간 기준과
+#  반대로 뒤집히는 문제가 있었음. 이제 "이번 이동과 같은 거리"를 갔다면 수단별로
+#  얼마나 배출하는지 비교한다.)
+st.subheader(f"💡 이번 이동 거리(약 {trip_distance_km:g}km)를 다른 수단으로 갔다면?")
+df_all["비교배출량(g)"] = df_all["1km당 CO2 배출량(g)"] * trip_distance_km
+
+# 배출량 큰 것부터 위에서 아래로 나오도록 순서를 직접 지정
+# (color로 묶으면 정렬한 데이터프레임 순서가 그대로 안 먹히는 경우가 있어
+#  category_orders로 명시적으로 y축 순서를 고정)
+order_desc = df_all.sort_values("비교배출량(g)", ascending=False)["교통수단"].tolist()
+
 fig_bar = px.bar(
-    df_all.sort_values("비교배출량(g)"),
+    df_all,
     x="비교배출량(g)", y="교통수단",
     color="카테고리",
     color_discrete_map=COLOR_MAP,
-    orientation="h"
+    orientation="h",
+    category_orders={"교통수단": order_desc}
 )
 fig_bar.update_layout(
-    height=350,
+    height=380,
     margin=dict(l=0, r=20, t=10, b=10),
     xaxis_title="비교배출량(g)", yaxis_title=""
 )
 st.plotly_chart(fig_bar, use_container_width=True)
 
-# 감축 효과 — 수정된 로직
+# 감축 효과 — 같은 거리 기준으로 KTX 전환 시 절감량 계산
 st.subheader("🌱 전환 시 감축 효과")
-train_score_per_hour = transport_score_map["고속열차 (KTX/SRT)"]
-train_kg = round(train_score_per_hour * time_hours * multiplier, 2)
+train_g_km = df_all.loc[df_all["교통수단"] == "고속열차 (KTX/SRT)", "1km당 CO2 배출량(g)"].iloc[0]
+train_kg = round(train_g_km * trip_distance_km / 1000, 2)
 reduction_kg = round(long_kg - train_kg, 2)
 
 if selected_transport in LOW_CARBON:
@@ -237,9 +250,18 @@ fig_donut.update_layout(
 )
 st.plotly_chart(fig_donut, use_container_width=True)
 
+with st.expander("📎 배출계수 출처 보기"):
+    st.dataframe(
+        df_all[["교통수단", "1km당 CO2 배출량(g)", "평균시속(km/h)", "출처"]],
+        use_container_width=True, hide_index=True
+    )
+
 st.markdown("---")
 st.caption(
-    "📱 탄소여권 프로젝트 | 제비여행 × 이매진피스\n"
-    "연간 예산 기준: 녹색전환연구소 1.5°C 라이프스타일 계산기 (15lifestyle.or.kr)\n"
-    "출처: KOTEMS · 환경부 · 한국철도공사 ESG · Cornell CHSB · Poore & Nemecek 2018 · ICAO"
+    "📱 탄소여권 프로젝트 | 제비여행 × 이매진피스\n\n"
+    "연간 예산 기준: 녹색전환연구소 1.5°C 라이프스타일 계산기 (15lifestyle.or.kr)\n\n"
+    "장거리 이동 배출계수 출처: 한국철도공사 2022 환경경영보고서·환경부 탄소성적표지(KTX) · "
+    "ICAO ICEC(항공) · DEFRA/DESNZ 2025(고속버스·일반기차) · "
+    "ITF, 1.5°C 라이프스타일 가이드북·녹색전환연구소(도시내 대중교통·자가용)\n\n"
+    "⚠️ 일반기차·국제선 항공·자가용(장거리)의 평균 속도 가정은 공식 출처 확인 전 잠정치입니다."
 )
