"""
차트 생성 모듈
"""
import altair as alt


def create_line_chart(df_station, selected_station, selected_direction, meta_col_운행구분, all_times):
    """
    시간대별 혼잡도 라인차트 생성 (단일 역)
    
    Parameters:
    -----------
    df_station : pd.DataFrame
        특정 역의 데이터
    selected_station : str
        선택된 역명
    selected_direction : str
        선택된 운행구분
    meta_col_운행구분 : str
        운행구분 컬럼명
    all_times : list
        시간 순서 리스트
    
    Returns:
    --------
    alt.Chart
        Altair 라인차트
    """
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
    
    return chart


def create_comparison_chart(df_compare, selected_stations, selected_direction, meta_col_역명, meta_col_운행구분, all_times):
    """
    역 비교 라인차트 생성 (여러 역)
    
    Parameters:
    -----------
    df_compare : pd.DataFrame
        비교할 역들의 데이터
    selected_stations : list
        선택된 역명 리스트
    selected_direction : str
        선택된 운행구분
    meta_col_역명 : str
        역명 컬럼명
    meta_col_운행구분 : str
        운행구분 컬럼명
    all_times : list
        시간 순서 리스트
    
    Returns:
    --------
    alt.Chart
        Altair 라인차트
    """
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
            width=800,
            height=400,
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
            width=800,
            height=400,
            title=f'역 비교: {", ".join(selected_stations)} ({selected_direction})'
        )
    
    return chart


def create_ranking_bar_chart(ranking, meta_col_역명, meta_col_운행구분):
    """
    랭킹 막대 차트 생성
    
    Parameters:
    -----------
    ranking : pd.DataFrame
        랭킹 데이터 (상위 10개)
    meta_col_역명 : str
        역명 컬럼명
    meta_col_운행구분 : str
        운행구분 컬럼명
    
    Returns:
    --------
    alt.Chart
        Altair 막대차트
    """
    chart = alt.Chart(ranking).mark_bar().encode(
        x=alt.X('peak:Q', title='피크 혼잡도'),
        y=alt.Y(f'{meta_col_역명}:N', title='역명', sort='-x'),
        color=alt.Color('peak:Q', scale=alt.Scale(scheme='reds'), legend=None),
        tooltip=[meta_col_역명, meta_col_운행구분, 'peak', 'peak_time']
    ).properties(
        width=700,
        height=400
    )
    
    return chart


def create_heatmap(df_heatmap, selected_line, meta_col_역명, meta_col_운행구분, station_order, all_times, max_stations):
    """
    혼잡도 히트맵 생성
    
    Parameters:
    -----------
    df_heatmap : pd.DataFrame
        히트맵용 데이터
    selected_line : str
        선택된 호선
    meta_col_역명 : str
        역명 컬럼명
    meta_col_운행구분 : str
        운행구분 컬럼명
    station_order : list
        역 정렬 순서
    all_times : list
        시간 순서 리스트
    max_stations : int
        표시할 최대 역 수
    
    Returns:
    --------
    alt.Chart
        Altair 히트맵
    """
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
        width=800,
        height=max(400, max_stations * 20),  # 역 수에 따라 높이 조정
        title=f'{selected_line} 혼잡도 히트맵'
    )
    
    return heatmap
