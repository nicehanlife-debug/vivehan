import streamlit as st
import pandas as pd
import altair as alt
from datetime import time

# 페이지 설정
st.set_page_config(
    page_title="서울교통공사 지하철 혼잡도 대시보드",
    page_icon="🚇",
    layout="wide"
)

# ==================== 데이터 로딩 및 전처리 ====================

@st.cache_data
def load_data():
    """CSV 파일을 로딩하고 long 형태로 변환"""
    csv_file = '서울교통공사_지하철혼잡도정보_20250930.csv'
    
    # 인코딩 자동 시도
    for encoding in ['cp949', 'euc-kr', 'utf-8-sig', 'utf-8']:
        try:
            df = pd.read_csv(csv_file, encoding=encoding)
            break
        except:
            continue
    else:
        st.error("CSV 파일을 읽을 수 없습니다. 인코딩 문제를 확인하세요.")
        return None
    
    # 컬럼명 정리
    df.columns = df.columns.str.strip()
    
    # 메타 컬럼 (처음 5개)
    meta_cols = df.columns[:5].tolist()
    time_cols = df.columns[5:].tolist()
    
    # 시간 컬럼을 HH:MM 형태로 변환하는 매핑
    time_mapping = {}
    for col in time_cols:
        # "5시30분" -> "05:30" 형태로 변환
        col_clean = col.replace('시', ':').replace('분', '').strip()
        parts = col_clean.split(':')
        if len(parts) == 2:
            hour = parts[0].zfill(2)
            minute = parts[1].zfill(2)
            time_mapping[col] = f"{hour}:{minute}"
    
    # wide -> long 변환
    df_long = df.melt(
        id_vars=meta_cols,
        value_vars=time_cols,
        var_name='time_original',
        value_name='crowding'
    )
    
    # 시간 표준화
    df_long['time'] = df_long['time_original'].map(time_mapping)
    
    # 혼잡도 값을 float로 변환 (공백 제거)
    df_long['crowding'] = pd.to_numeric(
        df_long['crowding'].astype(str).str.strip().str.replace(',', ''),
        errors='coerce'
    )
    
    # 시간 정렬을 위한 시간 순서 컬럼 추가
    def time_to_minutes(t):
        """HH:MM을 분 단위로 변환 (00:00~00:30은 24시간 이후로 처리)"""
        if pd.isna(t):
            return None
        h, m = map(int, t.split(':'))
        if h == 0:  # 자정 이후는 24시간 더하기
            h = 24
        return h * 60 + m
    
    df_long['time_order'] = df_long['time'].apply(time_to_minutes)
    
    # 결측치 제거
    df_long = df_long.dropna(subset=['crowding', 'time', 'time_order'])
    
    return df_long

# ==================== 데이터 로드 ====================

df = load_data()

if df is None:
    st.stop()

# 컬럼명 확인
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

# 선택된 호선의 데이터만 필터링
df_filtered = df[df[meta_col_호선] == selected_line].copy()

# 역 필터
stations = ['전체'] + sorted(df_filtered[meta_col_역명].unique().tolist())
selected_station = st.sidebar.selectbox(
    "역 선택",
    options=stations,
    index=0
)

# 운행구분 필터
directions = ['전체'] + sorted(df_filtered[meta_col_운행구분].unique().tolist())
selected_direction = st.sidebar.selectbox(
    "운행구분",
    options=directions,
    index=0
)

# 시간 범위 필터
# time_order 기준으로 정렬하여 올바른 시간 순서 보장
all_times_df = df[['time', 'time_order']].drop_duplicates().sort_values('time_order')
all_times = all_times_df['time'].tolist()

st.sidebar.subheader("시간대 범위")
time_range = st.sidebar.select_slider(
    "시간 선택",
    options=all_times,
    value=(all_times[0], all_times[-1])
)

# Top N 설정
top_n = st.sidebar.number_input(
    "랭킹 Top N",
    min_value=5,
    max_value=50,
    value=20,
    step=5
)

# ==================== 필터 적용 ====================

# 운행구분 필터 적용
if selected_direction != '전체':
    df_filtered = df_filtered[df_filtered[meta_col_운행구분] == selected_direction]

# 시간 범위 필터 적용
time_start_minutes = int(df_filtered[df_filtered['time'] == time_range[0]]['time_order'].iloc[0])
time_end_minutes = int(df_filtered[df_filtered['time'] == time_range[1]]['time_order'].iloc[0])
df_filtered = df_filtered[
    (df_filtered['time_order'] >= time_start_minutes) & 
    (df_filtered['time_order'] <= time_end_minutes)
]

# ==================== 탭 구성 ====================

tab1, tab2 = st.tabs(["📍 역 상세", "🏆 랭킹"])

# ==================== 탭 1: 역 상세 ====================

with tab1:
    st.header("역별 시간대 혼잡도 상세")
    
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
            if selected_direction == '전체':
                # 운행구분별로 색상 분리
                chart = alt.Chart(df_station).mark_line(point=True).encode(
                    x=alt.X('time:N', title='시간', sort=all_times),
                    y=alt.Y('crowding:Q', title='혼잡도'),
                    color=alt.Color(f'{meta_col_운행구분}:N', title='운행구분'),
                    tooltip=['time:N', 'crowding:Q', f'{meta_col_운행구분}:N']
                ).properties(
                    width=800,
                    height=400,
                    title=f'{selected_station} 시간대별 혼잡도'
                )
            else:
                # 단일 라인
                chart = alt.Chart(df_station).mark_line(point=True).encode(
                    x=alt.X('time:N', title='시간', sort=all_times),
                    y=alt.Y('crowding:Q', title='혼잡도'),
                    tooltip=['time:N', 'crowding:Q']
                ).properties(
                    width=800,
                    height=400,
                    title=f'{selected_station} ({selected_direction}) 시간대별 혼잡도'
                )
            
            st.altair_chart(chart, use_container_width=True)
            
            # 데이터 테이블
            with st.expander("상세 데이터 보기"):
                display_cols = [meta_col_역명, meta_col_운행구분, 'time', 'crowding']
                st.dataframe(
                    df_station[display_cols].sort_values('time_order'),
                    hide_index=True
                )

# ==================== 탭 2: 랭킹 ====================

with tab2:
    st.header("혼잡도 랭킹")
    
    if df_filtered.empty:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
    else:
        # 역별/운행구분별로 피크값 계산
        ranking = df_filtered.groupby([meta_col_역명, meta_col_역번호, meta_col_운행구분]).agg({
            'crowding': ['max', 'mean']
        }).reset_index()
        
        ranking.columns = [meta_col_역명, meta_col_역번호, meta_col_운행구분, 'peak', 'avg']
        
        # 피크 시간 찾기
        def get_peak_time(row):
            station_data = df_filtered[
                (df_filtered[meta_col_역명] == row[meta_col_역명]) &
                (df_filtered[meta_col_운행구분] == row[meta_col_운행구분])
            ]
            if not station_data.empty:
                return station_data.loc[station_data['crowding'].idxmax(), 'time']
            return None
        
        ranking['peak_time'] = ranking.apply(get_peak_time, axis=1)
        
        # 피크 기준 정렬
        ranking = ranking.sort_values('peak', ascending=False).head(top_n)
        
        # 순위 추가
        ranking.insert(0, '순위', range(1, len(ranking) + 1))
        
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
        
        # 상위 10개 역 막대 차트
        st.subheader("상위 역 시각화")
        top_10 = ranking.head(10)
        
        chart = alt.Chart(top_10).mark_bar().encode(
            x=alt.X('peak:Q', title='피크 혼잡도'),
            y=alt.Y(f'{meta_col_역명}:N', title='역명', sort='-x'),
            color=alt.Color('peak:Q', scale=alt.Scale(scheme='reds'), legend=None),
            tooltip=[meta_col_역명, meta_col_운행구분, 'peak', 'peak_time']
        ).properties(
            width=700,
            height=400
        )
        
        st.altair_chart(chart, use_container_width=True)

# ==================== 푸터 ====================

st.markdown("---")
st.caption("데이터 출처: 서울교통공사 지하철 혼잡도 정보 (2025.09.30)")
