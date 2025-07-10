# 📚 Google Scholar Profile Crawler

> 교수들의 Google Scholar 프로필에서 사진, 소속, 키워드, 상위 논문 정보를 수집해 CSV로 저장하는 자동화 스크립트입니다.

---

## 🔍 기능 개요

이 스크립트는 `top_400_with_scholarurl.csv` 파일에 저장된 교수들의 **Google Scholar 프로필 URL**을 기반으로 다음 정보를 수집합니다:

- 📸 **프로필 사진 URL**
- 🏫 **소속(affiliation)**
- 🔖 **연구 키워드**
- 📄 **상위 논문 3개** (제목 + 링크)

크롤링된 정보는 기존 데이터와 병합되어 `final_scholar_results.csv`로 저장됩니다.

---

## 📁 입력 파일

**top_400_with_scholarurl.csv**

| name       | profile_url                         |
|------------|--------------------------------------|
| John Doe   | https://scholar.google.com/citations?user=abc |

> `profile_url` 컬럼은 Google Scholar의 공개 프로필 URL이어야 합니다.

---

## ⚙️ 사용 기술

- `Selenium` – 동적 페이지 렌더링
- `BeautifulSoup` – HTML 파싱
- `Pandas` – CSV 읽기/쓰기
- `webdriver-manager` – ChromeDriver 자동 관리

---

## 🛠️ 실행 방법

```bash
# 가상환경 설정 (선택)
python -m venv venv
source venv/bin/activate  # 또는 venv\Scripts\activate (Windows)

# 필요한 패키지 설치
pip install pandas selenium beautifulsoup4 webdriver-manager

# 실행
python findora.py
```

# 출력 파일
### final_scholar_results.csv

| name     | image_url | affiliation_from_scholar | keywords                   | top_papers                             |
|----------|-----------|---------------------------|----------------------------|----------------------------------------|
| John Doe | ...       | MIT                       | machine learning; robotics | Paper1 (링크); Paper2 (링크); ...      |

# 주의사항
- Scholar 페이지 구조 변경 시 크롤링이 실패할 수 있습니다.
- profile_url이 비어 있거나 유효하지 않으면 해당 행은 건너뜁니다.
- 과도한 요청은 Google Scholar에서 차단될 수 있으므로 요청 간 1.5초 딜레이를 유지하세요.
- headless 모드로 실행되므로 실제 브라우저는 뜨지 않습니다.