"""
데이터 로딩 및 전처리 모듈

이 모듈은 서울교통공사 지하철 혼잡도 CSV 데이터를 로드하고,
분석에 적합한 형태로 전처리하는 기능을 제공합니다.
"""
from typing import Optional, Tuple, List
import streamlit as st
import pandas as pd

# ==================== 상수 정의 ====================
DEFAULT_CSV_FILE = '서울교통공사_지하철혼잡도정보_20250930.csv'
DEFAULT_ENCODING = 'cp949'
ENCODING_OPTIONS = ['cp949', 'euc-kr', 'utf-8-sig', 'utf-8']
DEFAULT_TOP_N = 20
MIDNIGHT_HOUR = 24  # 자정 이후 시간 처리를 위한 상수


@st.cache_data
def load_data(csv_file: str = DEFAULT_CSV_FILE) -> Optional[pd.DataFrame]:
    """
    지하철 혼잡도 CSV 파일을 로드하고 long 형태로 전처리합니다.
    
    이 함수는 다음 작업을 수행합니다:
    1. 여러 인코딩 옵션을 시도하여 CSV 파일 로드
    2. wide format(시간 컬럼 여러 개)을 long format으로 변환
    3. 시간 컬럼을 HH:MM 표준 형식으로 변환
    4. 혼잡도 값을 숫자형으로 변환 및 결측치 제거
    
    Args:
        csv_file: CSV 파일 경로. 기본값은 DEFAULT_CSV_FILE.
    
    Returns:
        전처리된 DataFrame (long format). 로딩 실패 시 None 반환.
        컬럼: [운영기관, 호선, 역번호, 역명, 운행구분, time_original, crowding, time, time_order]
    
    Raises:
        None. 에러 발생 시 Streamlit 에러 메시지를 표시하고 None 반환.
    
    Examples:
        >>> df = load_data()
        >>> print(df.columns)
        ['운영기관', '호선', '역번호', '역명', '운행구분', 'time_original', 'crowding', 'time', 'time_order']
    """
    df = None
    
    # 여러 인코딩 옵션 시도
    for encoding in ENCODING_OPTIONS:
        try:
            df = pd.read_csv(csv_file, encoding=encoding)
            break
        except FileNotFoundError:
            st.error(f"❌ 파일을 찾을 수 없습니다: {csv_file}")
            st.info("💡 파일 경로를 확인하거나, 파일이 프로젝트 폴더에 있는지 확인하세요.")
            return None
        except UnicodeDecodeError:
            continue  # 다음 인코딩 시도
        except Exception as e:
            st.error(f"❌ 파일 로딩 중 오류 발생: {str(e)}")
            return None
    
    if df is None:
        st.error(f"❌ CSV 파일을 읽을 수 없습니다. 지원하는 인코딩: {', '.join(ENCODING_OPTIONS)}")
        st.info("💡 파일을 텍스트 편집기로 열어 인코딩을 확인하거나, UTF-8로 저장한 후 다시 시도하세요.")
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
    def time_to_minutes(t: str) -> Optional[int]:
        """
        HH:MM 형식의 시간을 분 단위 정수로 변환합니다.
        
        자정(00:XX)은 24시간 이후로 처리하여 시간 순서를 올바르게 유지합니다.
        예: 00:30 -> 1470분 (24*60 + 30)
        
        Args:
            t: HH:MM 형식의 시간 문자열
        
        Returns:
            분 단위 정수. 입력이 None이거나 유효하지 않으면 None 반환.
        """
        if pd.isna(t):
            return None
        try:
            h, m = map(int, t.split(':'))
            if h == 0:  # 자정 이후는 24시간 더하기
                h = MIDNIGHT_HOUR
            return h * 60 + m
        except (ValueError, AttributeError):
            return None
    
    df_long['time_order'] = df_long['time'].apply(time_to_minutes)
    
    # 결측치 제거 및 데이터 검증
    initial_rows = len(df_long)
    df_long = df_long.dropna(subset=['crowding', 'time', 'time_order'])
    final_rows = len(df_long)
    
    if final_rows == 0:
        st.error("❌ 유효한 데이터가 없습니다. CSV 파일 내용을 확인하세요.")
        return None
    
    # 데이터 로딩 성공 로그 (디버그용, 필요시 주석 해제)
    # removed_rows = initial_rows - final_rows
    # if removed_rows > 0:
    #     st.info(f"ℹ️ 결측치 {removed_rows}개 행이 제거되었습니다.")
    
    return df_long


def get_filtered_data(
    df: pd.DataFrame,
    line: Optional[str] = None,
    direction: Optional[str] = None,
    time_range: Optional[Tuple[str, str]] = None
) -> pd.DataFrame:
    """
    필터 조건에 따라 데이터를 필터링합니다.
    
    Args:
        df: 전체 데이터프레임
        line: 호선명 (예: '1호선'). None이면 필터링하지 않음.
        direction: 운행구분 (예: '상행', '하행', '전체'). '전체' 또는 None이면 필터링하지 않음.
        time_range: 시간 범위 튜플 (시작시간, 종료시간). 예: ('05:30', '09:00')
    
    Returns:
        필터링된 데이터프레임. 조건에 맞는 데이터가 없으면 빈 DataFrame 반환.
    
    Examples:
        >>> df_filtered = get_filtered_data(df, line='1호선', direction='상행', time_range=('07:00', '09:00'))
    """
    if df is None or df.empty:
        return pd.DataFrame()
    
    df_filtered = df.copy()
    col_names = df.columns.tolist()
    
    # 호선 필터
    if line:
        if len(col_names) < 2:
            return pd.DataFrame()
        meta_col_호선 = col_names[1]
        df_filtered = df_filtered[df_filtered[meta_col_호선] == line]
    
    # 운행구분 필터
    if direction and direction != '전체':
        if len(col_names) < 5:
            return pd.DataFrame()
        meta_col_운행구분 = col_names[4]
        df_filtered = df_filtered[df_filtered[meta_col_운행구분] == direction]
    
    # 시간 범위 필터
    if time_range and len(time_range) == 2:
        start_time, end_time = time_range
        if not df_filtered.empty:
            try:
                # 시작/종료 시간의 time_order 값 찾기
                time_start_df = df_filtered[df_filtered['time'] == start_time]
                time_end_df = df_filtered[df_filtered['time'] == end_time]
                
                if not time_start_df.empty and not time_end_df.empty:
                    time_start_minutes = int(time_start_df['time_order'].iloc[0])
                    time_end_minutes = int(time_end_df['time_order'].iloc[0])
                    df_filtered = df_filtered[
                        (df_filtered['time_order'] >= time_start_minutes) & 
                        (df_filtered['time_order'] <= time_end_minutes)
                    ]
            except (KeyError, IndexError, ValueError):
                # 시간 범위 필터링 실패 시 원본 반환
                pass
    
    return df_filtered


def calculate_ranking(
    df_filtered: pd.DataFrame,
    meta_col_역명: str,
    meta_col_역번호: str,
    meta_col_운행구분: str,
    top_n: int = DEFAULT_TOP_N
) -> pd.DataFrame:
    """
    역별 피크/평균 혼잡도 랭킹을 계산합니다.
    
    각 역의 운행구분별로 다음 지표를 계산합니다:
    - 피크 혼잡도: 시간대별 최대값
    - 평균 혼잡도: 시간대별 평균값
    - 피크 시간: 최대 혼잡도가 발생한 시간
    
    Args:
        df_filtered: 필터링된 데이터프레임
        meta_col_역명: 역명 컬럼명
        meta_col_역번호: 역번호 컬럼명
        meta_col_운행구분: 운행구분 컬럼명
        top_n: 반환할 상위 N개 역 수. 기본값은 DEFAULT_TOP_N.
    
    Returns:
        랭킹 데이터프레임. 컬럼: [순위, 역명, 역번호, 운행구분, peak, avg, peak_time]
        피크 혼잡도 기준 내림차순 정렬.
    
    Examples:
        >>> ranking = calculate_ranking(df, '역명', '역번호', '운행구분', top_n=10)
        >>> print(ranking[['순위', '역명', 'peak']].head())
    """
    if df_filtered is None or df_filtered.empty:
        return pd.DataFrame()
    
    # 역별/운행구분별로 피크값 계산
    try:
        ranking = df_filtered.groupby([meta_col_역명, meta_col_역번호, meta_col_운행구분]).agg({
            'crowding': ['max', 'mean']
        }).reset_index()
        
        ranking.columns = [meta_col_역명, meta_col_역번호, meta_col_운행구분, 'peak', 'avg']
    except KeyError as e:
        st.error(f"❌ 필수 컬럼을 찾을 수 없습니다: {e}")
        return pd.DataFrame()
    
    # 피크 시간 찾기
    def get_peak_time(row: pd.Series) -> Optional[str]:
        """각 역/운행구분의 피크 시간을 찾습니다."""
        try:
            station_data = df_filtered[
                (df_filtered[meta_col_역명] == row[meta_col_역명]) &
                (df_filtered[meta_col_운행구분] == row[meta_col_운행구분])
            ]
            if not station_data.empty:
                return station_data.loc[station_data['crowding'].idxmax(), 'time']
        except (KeyError, IndexError):
            pass
        return None
    
    ranking['peak_time'] = ranking.apply(get_peak_time, axis=1)
    
    # 피크 기준 정렬 및 상위 N개 선택
    ranking = ranking.sort_values('peak', ascending=False).head(top_n)
    
    # 순위 추가
    ranking.insert(0, '순위', range(1, len(ranking) + 1))
    
    return ranking


def get_station_peaks(df_filtered: pd.DataFrame, meta_col_역명: str) -> pd.DataFrame:
    """
    각 역별 피크 혼잡도를 계산합니다 (히트맵 정렬용).
    
    Args:
        df_filtered: 필터링된 데이터프레임
        meta_col_역명: 역명 컬럼명
    
    Returns:
        역별 피크 혼잡도 데이터프레임. 컬럼: [역명, peak_crowding]
    
    Examples:
        >>> station_peaks = get_station_peaks(df, '역명')
        >>> print(station_peaks.head())
    """
    if df_filtered is None or df_filtered.empty:
        return pd.DataFrame()
    
    try:
        station_peaks = df_filtered.groupby(meta_col_역명)['crowding'].max().reset_index()
        station_peaks.columns = [meta_col_역명, 'peak_crowding']
        return station_peaks
    except KeyError as e:
        st.error(f"❌ 필수 컬럼을 찾을 수 없습니다: {e}")
        return pd.DataFrame()
