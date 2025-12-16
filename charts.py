"""
차트 생성 모듈

이 모듈은 지하철 혼잡도 데이터를 시각화하는 Altair 차트를 생성합니다.
라인차트, 막대차트, 히트맵 등 다양한 시각화 기능을 제공합니다.
"""
from typing import List
import pandas as pd
import altair as alt

# ==================== 상수 정의 ====================
DEFAULT_CHART_WIDTH = 800
DEFAULT_CHART_HEIGHT = 400
HEATMAP_ROW_HEIGHT = 20  # 히트맵에서 역당 높이
MIN_HEATMAP_HEIGHT = 400


def create_line_chart(
    df_station: pd.DataFrame,
    selected_station: str,
    selected_direction: str,
    meta_col_운행구분: str,
    all_times: List[str]
) -> alt.Chart:
    """
    단일 역의 시간대별 혼잡도 라인차트를 생성합니다.
    
    운행구분이 '전체'인 경우 운행구분별로 색상을 분리하여 표시하고,
    특정 운행구분인 경우 단일 라인으로 표시합니다.
    
    Args:
        df_station: 특정 역의 데이터프레임
        selected_station: 선택된 역명
        selected_direction: 선택된 운행구분 ('전체', '상행', '하행' 등)
        meta_col_운행구분: 운행구분 컬럼명
        all_times: 시간 순서 리스트 (차트 x축 정렬용)
    
    Returns:
        Altair 라인차트 객체
    
    Examples:
        >>> chart = create_line_chart(df, '서울역', '상행', '운행구분', all_times)
        >>> st.altair_chart(chart)
    """
    if df_station is None or df_station.empty:
        # 빈 차트 반환
        return alt.Chart(pd.DataFrame()).mark_text().encode(
            text=alt.value("데이터가 없습니다")
        ).properties(width=DEFAULT_CHART_WIDTH, height=DEFAULT_CHART_HEIGHT)
    
    if selected_direction == '전체':
        # 운행구분별로 색상 분리
        chart = alt.Chart(df_station).mark_line(point=True).encode(
            x=alt.X('time:N', title='시간', sort=all_times),
            y=alt.Y('crowding:Q', title='혼잡도'),
            color=alt.Color(f'{meta_col_운행구분}:N', title='운행구분'),
            tooltip=['time:N', 'crowding:Q', f'{meta_col_운행구분}:N']
        ).properties(
            width=DEFAULT_CHART_WIDTH,
            height=DEFAULT_CHART_HEIGHT,
            title=f'{selected_station} 시간대별 혼잡도'
        )
    else:
        # 단일 라인
        chart = alt.Chart(df_station).mark_line(point=True).encode(
            x=alt.X('time:N', title='시간', sort=all_times),
            y=alt.Y('crowding:Q', title='혼잡도'),
            tooltip=['time:N', 'crowding:Q']
        ).properties(
            width=DEFAULT_CHART_WIDTH,
            height=DEFAULT_CHART_HEIGHT,
            title=f'{selected_station} ({selected_direction}) 시간대별 혼잡도'
        )
    
    return chart


def create_comparison_chart(
    df_compare: pd.DataFrame,
    selected_stations: List[str],
    selected_direction: str,
    meta_col_역명: str,
    meta_col_운행구분: str,
    all_times: List[str]
) -> alt.Chart:
    """
    여러 역의 혼잡도를 비교하는 라인차트를 생성합니다.
    
    운행구분이 '전체'인 경우 역별 색상 + 운행구분별 선 스타일로 구분하고,
    특정 운행구분인 경우 역별 색상으로만 구분합니다.
    
    Args:
        df_compare: 비교할 역들의 데이터프레임
        selected_stations: 선택된 역명 리스트
        selected_direction: 선택된 운행구분 ('전체', '상행', '하행' 등)
        meta_col_역명: 역명 컬럼명
        meta_col_운행구분: 운행구분 컬럼명
        all_times: 시간 순서 리스트 (차트 x축 정렬용)
    
    Returns:
        Altair 라인차트 객체
    
    Examples:
        >>> chart = create_comparison_chart(df, ['서울역', '강남역'], '상행', '역명', '운행구분', all_times)
        >>> st.altair_chart(chart)
    """
    if df_compare is None or df_compare.empty:
        # 빈 차트 반환
        return alt.Chart(pd.DataFrame()).mark_text().encode(
            text=alt.value("데이터가 없습니다")
        ).properties(width=DEFAULT_CHART_WIDTH, height=DEFAULT_CHART_HEIGHT)
    
    if selected_direction == '전체':
        # 역별 + 운행구분별로 구분
        chart = alt.Chart(df_compare).mark_line(point=True).encode(
            x=alt.X('time:N', title='시간', sort=all_times),
            y=alt.Y('crowding:Q', title='혼잡도'),
            color=alt.Color(f'{meta_col_역명}:N', title='역명'),
            strokeDash=alt.StrokeDash(f'{meta_col_운행구분}:N', title='운행구분'),
            tooltip=[
                alt.Tooltip(f'{meta_col_역명}:N', title='역명'),
                alt.Tooltip('time:N', title='시간'),
                alt.Tooltip('crowding:Q', title='혼잡도', format='.1f'),
                alt.Tooltip(f'{meta_col_운행구분}:N', title='운행구분')
            ]
        ).properties(
            width=DEFAULT_CHART_WIDTH,
            height=DEFAULT_CHART_HEIGHT,
            title=f'역 비교: {", ".join(selected_stations)}'
        )
    else:
        # 역별로만 구분
        chart = alt.Chart(df_compare).mark_line(point=True).encode(
            x=alt.X('time:N', title='시간', sort=all_times),
            y=alt.Y('crowding:Q', title='혼잡도'),
            color=alt.Color(f'{meta_col_역명}:N', title='역명'),
            tooltip=[
                alt.Tooltip(f'{meta_col_역명}:N', title='역명'),
                alt.Tooltip('time:N', title='시간'),
                alt.Tooltip('crowding:Q', title='혼잡도', format='.1f')
            ]
        ).properties(
            width=DEFAULT_CHART_WIDTH,
            height=DEFAULT_CHART_HEIGHT,
            title=f'역 비교: {", ".join(selected_stations)} ({selected_direction})'
        )
    
    return chart


def create_ranking_bar_chart(
    ranking: pd.DataFrame,
    meta_col_역명: str,
    meta_col_운행구분: str
) -> alt.Chart:
    """
    혼잡도 랭킹 막대 차트를 생성합니다.
    
    피크 혼잡도를 기준으로 역을 정렬하고, 막대 색상으로 혼잡도를 표현합니다.
    
    Args:
        ranking: 랭킹 데이터프레임 (상위 10개 또는 N개)
        meta_col_역명: 역명 컬럼명
        meta_col_운행구분: 운행구분 컬럼명
    
    Returns:
        Altair 막대차트 객체
    
    Examples:
        >>> chart = create_ranking_bar_chart(top_10, '역명', '운행구분')
        >>> st.altair_chart(chart)
    """
    if ranking is None or ranking.empty:
        # 빈 차트 반환
        return alt.Chart(pd.DataFrame()).mark_text().encode(
            text=alt.value("랭킹 데이터가 없습니다")
        ).properties(width=700, height=DEFAULT_CHART_HEIGHT)
    
    chart = alt.Chart(ranking).mark_bar().encode(
        x=alt.X('peak:Q', title='피크 혼잡도'),
        y=alt.Y(f'{meta_col_역명}:N', title='역명', sort='-x'),
        color=alt.Color('peak:Q', scale=alt.Scale(scheme='reds'), legend=None),
        tooltip=[meta_col_역명, meta_col_운행구분, 'peak', 'peak_time']
    ).properties(
        width=700,
        height=DEFAULT_CHART_HEIGHT
    )
    
    return chart


def create_heatmap(
    df_heatmap: pd.DataFrame,
    selected_line: str,
    meta_col_역명: str,
    meta_col_운행구분: str,
    station_order: List[str],
    all_times: List[str],
    max_stations: int
) -> alt.Chart:
    """
    역별 × 시간대별 혼잡도 히트맵을 생성합니다.
    
    색상의 진하기로 혼잡도를 표현하며, 역 수에 따라 높이가 자동 조정됩니다.
    
    Args:
        df_heatmap: 히트맵용 데이터프레임
        selected_line: 선택된 호선명
        meta_col_역명: 역명 컬럼명
        meta_col_운행구분: 운행구분 컬럼명
        station_order: 역 정렬 순서 리스트 (y축 순서)
        all_times: 시간 순서 리스트 (x축 순서)
        max_stations: 표시할 최대 역 수
    
    Returns:
        Altair 히트맵 객체
    
    Examples:
        >>> heatmap = create_heatmap(df, '1호선', '역명', '운행구분', station_list, time_list, 20)
        >>> st.altair_chart(heatmap)
    """
    if df_heatmap is None or df_heatmap.empty:
        # 빈 차트 반환
        return alt.Chart(pd.DataFrame()).mark_text().encode(
            text=alt.value("히트맵 데이터가 없습니다")
        ).properties(width=DEFAULT_CHART_WIDTH, height=DEFAULT_CHART_HEIGHT)
    
    # 역 수에 따라 높이 조정 (최소 MIN_HEATMAP_HEIGHT)
    chart_height = max(MIN_HEATMAP_HEIGHT, max_stations * HEATMAP_ROW_HEIGHT)
    
    heatmap = alt.Chart(df_heatmap).mark_rect().encode(
        x=alt.X('time:O', title='시간', sort=all_times),
        y=alt.Y(f'{meta_col_역명}:N', title='역명', sort=station_order),
        color=alt.Color(
            'crowding:Q',
            scale=alt.Scale(scheme='reds'),
            title='혼잡도'
        ),
        tooltip=[
            alt.Tooltip(f'{meta_col_역명}:N', title='역명'),
            alt.Tooltip('time:O', title='시간'),
            alt.Tooltip('crowding:Q', title='혼잡도', format='.1f'),
            alt.Tooltip(f'{meta_col_운행구분}:N', title='운행구분')
        ]
    ).properties(
        width=DEFAULT_CHART_WIDTH,
        height=chart_height,
        title=f'{selected_line} 혼잡도 히트맵'
    )
    
    return heatmap
