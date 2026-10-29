# 원/달러 환율 추이 분석

첨부한 FRED `DEXKOUS.csv`를 분석해 최근 약 5년의 원/달러 환율 추세를 살펴보는 학습 프로젝트입니다. 분석 방법과 관찰/해석 구분은 [REPORT.md](REPORT.md)를 참고하세요.

## 프로젝트 파일

```text
.
├── analyze.py
├── data/
│   └── DEXKOUS.csv
├── images/
│   ├── 01_daily_and_moving_average.svg
│   ├── 02_monthly_average.svg
│   └── 03_monthly_change.svg
├── REPORT.md
└── requirements.txt
```

## 실행 방법

Python 3.10 이상이 필요합니다. 외부 라이브러리를 사용하지 않으므로 프로젝트 폴더에서 아래 명령만 실행하면 됩니다.

```bash
python analyze.py
```

그래프는 `images/`에 SVG 형식으로 생성됩니다. 최신 원자료로 갱신하려면 FRED에서 `DEXKOUS` CSV를 받아 `data/DEXKOUS.csv`에 덮어쓰세요. 분석 기간은 스크립트의 `START`, `END` 값으로 조정할 수 있습니다.

## 데이터와 라이선스 안내

데이터 시리즈: [FRED DEXKOUS](https://fred.stlouisfed.org/series/DEXKOUS). 원천은 미국 연방준비제도 이사회의 H.10 환율 자료이며, 뉴욕 기준 정오 매입 환율입니다. FRED는 출처 인용을 요청합니다. 데이터의 이용·재배포 조건은 원천의 최신 저작권 안내를 확인하세요. 본 프로젝트는 교육용이며 투자 조언이 아닙니다.

## 재현 환경

- Python 3.12.14에서 분석 스크립트 실행
- 최소 요구 버전: Python 3.10
- 외부 패키지: 없음 (Python 표준 라이브러리만 사용)
- 과제용 분석 리포트: [REPORT.md](REPORT.md)
