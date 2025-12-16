"""
서울교통공사 지하철 혼잡도 대시보드 메인 애플리케이션

이 Streamlit 앱은 지하철 혼잡도 데이터를 시각화하고 분석하는 대화형 대시보드입니다.

주요 기능:
- 호선/역/운행구분/시간대별 필터링
- 역 상세 분석 및 비교
- 혼잡도 랭킹
- 히트맵 시각화
- CSV 데이터 다운로드

작성일: 2024-12-16
버전: 1.0
"""
import streamlit as st
import pandas as pd
from data import load_data, calculate_ranking, get_station_peaks
from charts import create_line_chart, create_comparison_chart, create_ranking_bar_chart, create_heatmap

# ==================== 페이지 설정 ====================
st.set_page_config(
    page_title="서울교통공사 지하철 혼잡도 대시보드",
    page_icon="🚇",
    layout="wide"
)

# ==================== 데이터 로드 ====================

# CSV 파일 로드 및 전처리 (캐시됨)
df = load_data()

# 데이터 로딩 실패 시 앱 중단
if df is None:
    st.stop()

# 데이터 검증: 최소 컬럼 수 확인
if len(df.columns) < 5:
    st.error("❌ 데이터 형식이 올바르지 않습니다. 최소 5개 컬럼이 필요합니다.")
    st.stop()

# 메타 컬럼명 추출 (CSV 구조: 운영기관, 호선, 역번호, 역명, 운행구분, 시간 컬럼들...)
col_names = df.columns.tolist()
meta_col_운영기관 = col_names[0]
meta_col_호선 = col_names[1]
meta_col_역번호 = col_names[2]
meta_col_역명 = col_names[3]
meta_col_운행구분 = col_names[4]

# ==================== 헤더 ====================

st.title("🚇 서울교통공사 지하철 혼잡도 대시보드")
st.markdown("---")

# ==================== 사이드바 필터 ====================

st.sidebar.header("📊 필터 설정")

# 호선 필터
lines = sorted(df[meta_col_호선].unique())
selected_line = st.sidebar.selectbox(
    "호선 선택 (필수)",
    options=lines,
    index=0 if lines else None
)

# 선택된 호선의 데이터만 필터링 (이후 필터는 이 데이터 기준)
df_filtered = df[df[meta_col_호선] == selected_line].copy()

# 역 비교 모드 토글 (일반 모드 vs 비교 모드)
compare_mode = st.sidebar.checkbox("🔄 역 비교 모드", value=False)

# 역 필터
if compare_mode:
    # 비교 모드: 멀티셀렉트
    stations_list = sorted(df_filtered[meta_col_역명].unique().tolist())
    selected_stations = st.sidebar.multiselect(
        "비교할 역 선택 (최대 3개)",
        options=stations_list,
        default=[],
        max_selections=3
    )
    selected_station = None  # 비교 모드에서는 사용 안함
else:
    # 일반 모드: 단일 선택
    stations = ['전체'] + sorted(df_filtered[meta_col_역명].unique().tolist())
    selected_station = st.sidebar.selectbox(
        "역 선택",
        options=stations,
        index=0
    )
    selected_stations = []  # 일반 모드에서는 사용 안함

# 운행구분 필터
directions = ['전체'] + sorted(df_filtered[meta_col_운행구분].unique().tolist())
selected_direction = st.sidebar.selectbox(
    "운행구분",
    options=directions,
    index=0
)

# 시간 범위 필터
# time_order 기준으로 정렬하여 올바른 시간 순서 보장 (05:30 ~ 00:30)
all_times_df = df[['time', 'time_order']].drop_duplicates().sort_values('time_order')
all_times = all_times_df['time'].tolist()

st.sidebar.subheader("⏰ 시간대 범위")
time_range = st.sidebar.select_slider(
    "시간 선택",
    options=all_times,
    value=(all_times[0], all_times[-1])
)

# 랭킹 Top N 설정
top_n = st.sidebar.number_input(
    "🏆 랭킹 Top N",
    min_value=5,
    max_value=50,
    value=20,
    step=5,
    help="상위 N개 역을 랭킹에 표시합니다"
)

# ==================== 필터 적용 ====================

# 운행구분 필터 적용
if selected_direction != '전체':
    df_filtered = df_filtered[df_filtered[meta_col_운행구분] == selected_direction]

# 시간 범위 필터 적용
try:
    time_start_df = df_filtered[df_filtered['time'] == time_range[0]]
    time_end_df = df_filtered[df_filtered['time'] == time_range[1]]
    
    if not time_start_df.empty and not time_end_df.empty:
        time_start_minutes = int(time_start_df['time_order'].iloc[0])
        time_end_minutes = int(time_end_df['time_order'].iloc[0])
        df_filtered = df_filtered[
            (df_filtered['time_order'] >= time_start_minutes) & 
            (df_filtered['time_order'] <= time_end_minutes)
        ]
except (KeyError, IndexError, ValueError) as e:
    st.warning(f"⚠️ 시간 범위 필터링 중 오류가 발생했습니다: {e}")
    # 에러 발생 시 시간 필터링 없이 진행

# ==================== 탭 구성 ====================

tab1, tab2, tab3 = st.tabs(["📍 역 상세", "🏆 랭킹", "🔥 혼잡도 히트맵"])

# ==================== 탭 1: 역 상세 ====================

with tab1:
    st.header("역별 시간대 혼잡도 상세")
    
    # 비교 모드
    if compare_mode:
        if not selected_stations:
            st.info("👈 사이드바에서 비교할 역을 선택하세요 (최대 3개)")
        else:
            # 선택된 역들의 데이터
            df_compare = df_filtered[df_filtered[meta_col_역명].isin(selected_stations)].copy()
            
            if df_compare.empty:
                st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
            else:
                # 각 역별 KPI를 컬럼으로 표시
                cols = st.columns(len(selected_stations))
                
                for idx, station in enumerate(selected_stations):
                    df_station_temp = df_compare[df_compare[meta_col_역명] == station]
                    if not df_station_temp.empty:
                        with cols[idx]:
                            st.subheader(station)
                            peak_val = df_station_temp['crowding'].max()
                            avg_val = df_station_temp['crowding'].mean()
                            peak_t = df_station_temp.loc[df_station_temp['crowding'].idxmax(), 'time']
                            st.metric("피크", f"{peak_val:.1f}")
                            st.metric("평균", f"{avg_val:.1f}")
                            st.caption(f"피크 시간: {peak_t}")
                
                st.markdown("---")
                
                # 비교 라인차트
                chart = create_comparison_chart(
                    df_compare,
                    selected_stations,
                    selected_direction,
                    meta_col_역명,
                    meta_col_운행구분,
                    all_times
                )
                st.altair_chart(chart, use_container_width=True)
                
                # 데이터 테이블
                with st.expander("상세 데이터 보기"):
                    display_cols = [meta_col_역명, meta_col_운행구분, 'time', 'crowding']
                    st.dataframe(
                        df_compare.sort_values([meta_col_역명, 'time_order'])[display_cols],
                        hide_index=True
                    )
    
    # 일반 모드 (단일 역 선택)
    else:
        if selected_station == '전체':
            st.info("👈 사이드바에서 특정 역을 선택하면 상세 정보를 확인할 수 있습니다.")
        else:
            # 선택된 역의 데이터
            df_station = df_filtered[df_filtered[meta_col_역명] == selected_station].copy()
            
            if df_station.empty:
                st.warning(f"선택한 조건에 해당하는 데이터가 없습니다.")
            else:
                # KPI 표시
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    peak_value = df_station['crowding'].max()
                    st.metric("피크 혼잡도", f"{peak_value:.1f}")
                
                with col2:
                    peak_time = df_station.loc[df_station['crowding'].idxmax(), 'time']
                    st.metric("피크 시간", peak_time)
                
                with col3:
                    avg_value = df_station['crowding'].mean()
                    st.metric("평균 혼잡도", f"{avg_value:.1f}")
                
                st.markdown("---")
                
                # 라인차트
                chart = create_line_chart(
                    df_station,
                    selected_station,
                    selected_direction,
                    meta_col_운행구분,
                    all_times
                )
                st.altair_chart(chart, use_container_width=True)
                
                # 데이터 테이블
                with st.expander("상세 데이터 보기"):
                    display_cols = [meta_col_역명, meta_col_운행구분, 'time', 'crowding']
                    st.dataframe(
                        df_station.sort_values('time_order')[display_cols],
                        hide_index=True
                    )

# ==================== 탭 2: 랭킹 ====================

with tab2:
    st.header("혼잡도 랭킹")
    
    if df_filtered.empty:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
    else:
        # 랭킹 계산
        ranking = calculate_ranking(
            df_filtered,
            meta_col_역명,
            meta_col_역번호,
            meta_col_운행구분,
            top_n
        )
        
        # KPI
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("총 역 수", len(df_filtered[meta_col_역명].unique()))
        
        with col2:
            st.metric("최대 혼잡도", f"{df_filtered['crowding'].max():.1f}")
        
        with col3:
            st.metric("평균 혼잡도", f"{df_filtered['crowding'].mean():.1f}")
        
        st.markdown("---")
        
        # 랭킹 테이블
        st.subheader(f"Top {top_n} 혼잡 역")
        
        # 표시용 컬럼 정리
        display_ranking = ranking.copy()
        display_ranking['peak'] = display_ranking['peak'].round(1)
        display_ranking['avg'] = display_ranking['avg'].round(1)
        
        st.dataframe(
            display_ranking,
            hide_index=True,
            use_container_width=True,
            column_config={
                "순위": st.column_config.NumberColumn("순위", width="small"),
                meta_col_역명: st.column_config.TextColumn("역명", width="medium"),
                meta_col_역번호: st.column_config.TextColumn("역번호", width="small"),
                meta_col_운행구분: st.column_config.TextColumn("운행구분", width="small"),
                "peak": st.column_config.NumberColumn("피크 혼잡도", width="medium"),
                "avg": st.column_config.NumberColumn("평균 혼잡도", width="medium"),
                "peak_time": st.column_config.TextColumn("피크 시간", width="small"),
            }
        )
        
        # CSV 다운로드 버튼
        csv = display_ranking.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 랭킹 결과 다운로드 (CSV)",
            data=csv,
            file_name=f'지하철혼잡도_랭킹_{selected_line}_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mime='text/csv',
            use_container_width=True
        )
        
        st.markdown("---")
        
        # 상위 10개 역 막대 차트
        st.subheader("상위 역 시각화")
        top_10 = ranking.head(10)
        
        chart = create_ranking_bar_chart(top_10, meta_col_역명, meta_col_운행구분)
        st.altair_chart(chart, use_container_width=True)

# ==================== 탭 3: 혼잡도 히트맵 ====================

with tab3:
    st.header("혼잡도 히트맵")
    
    if df_filtered.empty:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
    else:
        # 히트맵 옵션
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.subheader("히트맵 설정")
            
            # 역 정렬 옵션
            sort_option = st.radio(
                "역 정렬 방식",
                options=["가나다순", "피크 혼잡도순"],
                index=0
            )
            
            # 최대 표시 역 수
            max_stations = st.slider(
                "표시할 최대 역 수",
                min_value=5,
                max_value=50,
                value=20,
                step=5
            )
        
        with col2:
            # 역별 피크 혼잡도 계산 (정렬용)
            station_peaks = get_station_peaks(df_filtered, meta_col_역명)
            
            # 정렬 방식에 따라 역 순서 결정
            if sort_option == "피크 혼잡도순":
                station_peaks = station_peaks.sort_values('peak_crowding', ascending=False)
            else:  # 가나다순
                station_peaks = station_peaks.sort_values(meta_col_역명)
            
            # 최대 역 수 제한
            top_stations = station_peaks.head(max_stations)[meta_col_역명].tolist()
            
            # 히트맵용 데이터 필터링
            df_heatmap = df_filtered[df_filtered[meta_col_역명].isin(top_stations)].copy()
            
            if df_heatmap.empty:
                st.warning("히트맵을 생성할 데이터가 없습니다.")
            else:
                # 역 순서 고정
                if sort_option == "피크 혼잡도순":
                    station_order = station_peaks.head(max_stations)[meta_col_역명].tolist()
                else:
                    station_order = sorted(top_stations)
                
                # 히트맵 생성
                heatmap = create_heatmap(
                    df_heatmap,
                    selected_line,
                    meta_col_역명,
                    meta_col_운행구분,
                    station_order,
                    all_times,
                    max_stations
                )
                st.altair_chart(heatmap, use_container_width=True)
                
                # 통계 정보
                st.markdown("---")
                st.subheader("혼잡도 통계")
                
                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                
                with col_stat1:
                    st.metric("표시 역 수", len(top_stations))
                
                with col_stat2:
                    st.metric("최대 혼잡도", f"{df_heatmap['crowding'].max():.1f}")
                
                with col_stat3:
                    st.metric("평균 혼잡도", f"{df_heatmap['crowding'].mean():.1f}")
                
                with col_stat4:
                    st.metric("최소 혼잡도", f"{df_heatmap['crowding'].min():.1f}")

# ==================== 푸터 ====================

st.markdown("---")
st.caption("데이터 출처: 서울교통공사 지하철 혼잡도 정보 (2025.09.30)")
