"""
데이터 로딩 및 전처리 모듈
"""
import streamlit as st
import pandas as pd


@st.cache_data
def load_data(csv_file='서울교통공사_지하철혼잡도정보_20250930.csv'):
    """CSV 파일을 로딩하고 long 형태로 변환"""
    
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


def get_filtered_data(df, line=None, direction=None, time_range=None):
    """
    필터 조건에 따라 데이터를 필터링
    
    Parameters:
    -----------
    df : pd.DataFrame
        전체 데이터
    line : str
        호선 (예: '1호선')
    direction : str
        운행구분 (예: '상행', '하행', '전체')
    time_range : tuple
        시간 범위 (start_time, end_time) 예: ('05:30', '09:00')
    
    Returns:
    --------
    pd.DataFrame
        필터링된 데이터
    """
    df_filtered = df.copy()
    
    # 호선 필터
    if line:
        col_names = df.columns.tolist()
        meta_col_호선 = col_names[1]
        df_filtered = df_filtered[df_filtered[meta_col_호선] == line]
    
    # 운행구분 필터
    if direction and direction != '전체':
        col_names = df.columns.tolist()
        meta_col_운행구분 = col_names[4]
        df_filtered = df_filtered[df_filtered[meta_col_운행구분] == direction]
    
    # 시간 범위 필터
    if time_range and len(time_range) == 2:
        start_time, end_time = time_range
        if not df_filtered.empty:
            time_start_minutes = int(df_filtered[df_filtered['time'] == start_time]['time_order'].iloc[0])
            time_end_minutes = int(df_filtered[df_filtered['time'] == end_time]['time_order'].iloc[0])
            df_filtered = df_filtered[
                (df_filtered['time_order'] >= time_start_minutes) & 
                (df_filtered['time_order'] <= time_end_minutes)
            ]
    
    return df_filtered


def calculate_ranking(df_filtered, meta_col_역명, meta_col_역번호, meta_col_운행구분, top_n=20):
    """
    역별 피크/평균 혼잡도 랭킹 계산
    
    Parameters:
    -----------
    df_filtered : pd.DataFrame
        필터링된 데이터
    meta_col_역명 : str
        역명 컬럼명
    meta_col_역번호 : str
        역번호 컬럼명
    meta_col_운행구분 : str
        운행구분 컬럼명
    top_n : int
        상위 N개 역
    
    Returns:
    --------
    pd.DataFrame
        랭킹 데이터 (순위, 역명, 역번호, 운행구분, peak, avg, peak_time 컬럼)
    """
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
    
    return ranking


def get_station_peaks(df_filtered, meta_col_역명):
    """
    각 역별 피크 혼잡도 계산 (히트맵용)
    
    Parameters:
    -----------
    df_filtered : pd.DataFrame
        필터링된 데이터
    meta_col_역명 : str
        역명 컬럼명
    
    Returns:
    --------
    pd.DataFrame
        역별 피크 혼잡도 (역명, peak_crowding 컬럼)
    """
    station_peaks = df_filtered.groupby(meta_col_역명)['crowding'].max().reset_index()
    station_peaks.columns = [meta_col_역명, 'peak_crowding']
    return station_peaks
