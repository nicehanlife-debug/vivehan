# 서울교통공사 지하철 혼잡도 대시보드

서울교통공사 지하철의 시간대별 혼잡도 정보를 시각화하는 Streamlit 대시보드입니다.

## 프로젝트 소개

이 프로젝트는 서울교통공사에서 제공하는 지하철 혼잡도 데이터(CSV)를 분석하고 시각화하여, 사용자가 특정 역과 시간대의 혼잡도를 쉽게 확인할 수 있도록 돕습니다.

### 주요 기능

#### Phase 1 (MVP 기능)
- **역별 상세 분석**: 특정 역의 시간대별 혼잡도를 라인차트로 시각화
- **혼잡도 랭킹**: 선택한 조건(호선/시간대/운행구분)에서 가장 혼잡한 역 Top N 표시
- **다양한 필터**: 호선, 역, 운행구분(상행/하행/내선/외선), 시간 범위 등 다양한 조건으로 데이터 필터링
- **인터랙티브 차트**: Altair를 활용한 인터랙티브 시각화

#### Phase 2 (분석력 강화)
- **혼잡도 히트맵**: 역 × 시간 매트릭스로 한눈에 혼잡 패턴 파악
- **역 비교 기능**: 최대 3개 역을 동시에 선택하여 시간대별 혼잡도 비교
- **CSV 다운로드**: 랭킹 결과를 CSV 파일로 다운로드

#### Phase 3 (코드 구조화)
- **모듈화된 코드**: 데이터 처리(`data.py`), 차트 생성(`charts.py`), UI(`app.py`)로 분리
- **유지보수성 향상**: 기능별로 구조화된 코드베이스

## 설치 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd vivehan-1
```

### 2. 가상환경 생성 및 활성화

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# 가상환경 활성화 (Windows CMD)
venv\Scripts\activate.bat

# 가상환경 활성화 (Linux/Mac)
source venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

## 사용 방법

### Streamlit 앱 실행

```bash
streamlit run app.py
```

앱 실행 후 브라우저에서 자동으로 열립니다 (기본: http://localhost:8501).

### 대시보드 사용법

1. **필터 설정** (좌측 사이드바)
   - **호선 선택**: 분석하고자 하는 호선 선택 (필수)
   - **비교 모드**: 여러 역을 동시에 비교하려면 체크
   - **역 선택**: 
     - 일반 모드: 단일 역 선택 (전체/특정역)
     - 비교 모드: 최대 3개 역 선택
   - **운행구분**: 상행/하행/내선/외선 또는 전체
   - **시간대 범위**: 분석하고자 하는 시간 범위 설정 (슬라이더)
   - **Top N**: 랭킹 탭에서 표시할 역 개수 (5~50)

2. **📍 역 상세 탭**
   - **일반 모드**: 선택한 역의 시간대별 혼잡도 라인차트
   - **비교 모드**: 선택한 여러 역을 하나의 차트에 표시
   - 피크 혼잡도, 피크 시간, 평균 혼잡도 KPI 표시
   - 운행구분이 "전체"인 경우 상/하행 비교 가능
   - 상세 데이터 테이블 제공 (확장 가능)

3. **🏆 랭킹 탭**
   - 현재 필터 조건에서 가장 혼잡한 역 Top N 표시
   - 순위, 피크 혼잡도, 평균 혼잡도, 피크 시간 정보 제공
   - 상위 10개 역 막대 차트 시각화
   - **CSV 다운로드**: 랭킹 결과를 CSV 파일로 다운로드 가능

4. **🔥 혼잡도 히트맵 탭**
   - 역 × 시간 매트릭스로 혼잡도 패턴 시각화
   - **정렬 옵션**: 가나다순 / 피크 혼잡도순
   - **표시 역 수**: 5~50개 역 슬라이더로 조정
   - 혼잡도 통계 (최대/평균/최소) 제공

## 데이터

- **출처**: 서울교통공사 지하철 혼잡도 정보
- **기준일**: 2025년 9월 30일
- **시간 범위**: 05:30 ~ 익일 00:30 (30분 간격)

## 기술 스택

- **Python 3.x**
- **Streamlit**: 웹 대시보드 프레임워크
- **Pandas**: 데이터 처리 및 분석
- **Altair**: 인터랙티브 데이터 시각화

## 프로젝트 구조

```
vivehan-1/
├── app.py                                          # Streamlit 메인 애플리케이션 (UI)
├── data.py                                         # 데이터 로딩 및 전처리 함수
├── charts.py                                       # 차트 생성 함수
├── requirements.txt                                # Python 의존성 (버전 고정)
├── README.md                                       # 프로젝트 문서
├── 대시보드_MVP_구현계획.md                        # 구현 계획 문서
└── 서울교통공사_지하철혼잡도정보_20250930.csv     # 원본 데이터
```

### 모듈 설명

- **`app.py`**: Streamlit UI 구성 및 사용자 인터랙션 처리
- **`data.py`**: CSV 로딩, 데이터 전처리, 필터링, 랭킹 계산
- **`charts.py`**: Altair 차트 생성 (라인차트, 히트맵, 막대차트)

## 개발 계획

전체 개발 계획은 `대시보드_MVP_구현계획.md` 파일을 참고하세요.

### Phase 1 (MVP) - 완료 ✅
- 데이터 로딩 및 전처리 (wide → long 변환)
- 기본 필터 구성 (호선, 역, 운행구분, 시간범위)
- 역 상세 분석 탭 (라인차트, KPI)
- 혼잡도 랭킹 탭 (Top N 테이블, 막대차트)

### Phase 2 (분석력 강화) - 완료 ✅
- 역×시간 혼잡도 히트맵 (정렬 옵션 포함)
- 여러 역 동시 비교 기능 (최대 3개)
- CSV 다운로드 기능 (랭킹 결과)

### Phase 3 (코드 구조화) - 완료 ✅
- 코드 모듈화 (`app.py`, `data.py`, `charts.py`)
- `requirements.txt` 버전 고정
- README 문서화 및 배포 옵션 정리

## 배포 옵션

### 1. Streamlit Community Cloud (권장)

**장점**: 무료, 가장 간단한 배포 방법

**단계**:
1. GitHub 레포지토리에 코드 푸시
2. [Streamlit Community Cloud](https://streamlit.io/cloud) 접속
3. "New app" 클릭 후 레포지토리 연결
4. `app.py` 선택 후 배포

**제약사항**:
- Public 레포지토리만 가능 (무료 계정)
- 리소스 제한 (메모리, CPU)

### 2. 로컬/사내 서버

**로컬 실행**:
```bash
streamlit run app.py
```

**특정 포트 지정**:
```bash
streamlit run app.py --server.port 8501
```

**외부 접근 허용**:
```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

### 3. Docker (선택사항)

**Dockerfile 예시**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

**Docker 실행**:
```bash
docker build -t subway-dashboard .
docker run -p 8501:8501 subway-dashboard
```

## 라이선스

MIT License
