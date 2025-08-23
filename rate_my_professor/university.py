# -*- coding: utf-8 -*-
"""
RMP + Google Scholar (Author) 통합 수집기 - 완성본
- Step1: RMP에서 교수 목록 수집 (이름/학과/점수/링크 등)
- Step2: Google Scholar '저자 검색' + '일반 검색' 2단계로 프로필 URL 탐색
- Step3: 프로필 상세(소속/키워드/상위 논문/이메일도메인/총인용) 파싱
- Step4: 병합 CSV 저장

필요 패키지:
  pip install selenium webdriver-manager beautifulsoup4 pandas
"""

import time, random, re
from typing import List, Dict, Optional
import pandas as pd

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ---------------------- 설정 ----------------------
BASE_RMP = "https://www.ratemyprofessors.com"
SCHOOL_SEARCH = BASE_RMP + "/search/schools?q={q}"
PROF_SEARCH   = BASE_RMP + "/search/professors/{sid}?q=*"

BASE_SCHOLAR = "https://scholar.google.com"
AUTHOR_SEARCH = BASE_SCHOLAR + "/citations?view_op=search_authors&hl=en&mauthors={q}"

SEARCH_KEYWORD = "harvard"     # 학교 키워드(예: "harvard")
MAX_PROFS      = 10            # RMP에서 몇 명까지

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


# ---------------------- 공통 ----------------------
def build_driver(headless=False):
    opts = Options()
    if headless:
        # Scholar가 headless에 민감할 수 있어 기본은 False 권장 (필요시 True)
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--lang=en")
    opts.add_argument(f"--user-agent={UA}")
    opts.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    driver.set_page_load_timeout(40)
    driver.set_script_timeout(40)
    return driver


def w8(driver, cond, timeout=15):
    return WebDriverWait(driver, timeout).until(cond)


def accept_scholar_consent(driver):
    """Google/Scholar 동의(콘센트) 화면이 있으면 통과"""
    try:
        driver.switch_to.default_content()
        # 페이지 안/iframe 안 모두 검사
        iframes = [None] + driver.find_elements(By.TAG_NAME, "iframe")
        for fr in iframes:
            try:
                driver.switch_to.default_content()
                if fr is not None:
                    driver.switch_to.frame(fr)
                # 'I agree' 버튼 또는 한국어 '동의' 버튼
                btns = driver.find_elements(
                    By.XPATH,
                    "//button[@id='L2AGLb' or .//div[text()='I agree'] or contains(., 'I agree') or contains(., '동의')]"
                )
                if btns:
                    btns[0].click()
                    time.sleep(1.5)
                    driver.switch_to.default_content()
                    return True
            except:
                driver.switch_to.default_content()
        driver.switch_to.default_content()
    except:
        driver.switch_to.default_content()
    return False


# ---------------------- RMP ----------------------
def get_first_school_id(driver, keyword: str) -> Optional[str]:
    from urllib.parse import quote
    url = SCHOOL_SEARCH.format(q=quote(keyword))
    driver.get(url)
    try:
        w8(driver, EC.presence_of_element_located((By.CSS_SELECTOR, "a[href^='/school/']")), timeout=20)
    except:
        return None
    links = driver.find_elements(By.CSS_SELECTOR, "a[href^='/school/']")
    if not links:
        return None
    href = links[0].get_attribute("href") or ""
    sid = href.rstrip("/").split("/")[-1]
    return sid if sid.isdigit() else None


def extract_text_safe(root, locators) -> Optional[str]:
    for by, sel in locators:
        try:
            els = root.find_elements(by, sel)
            if els:
                return els[0].text.strip()
        except:
            continue
    return None


def collect_professors(driver, school_id: str, limit: int = 10) -> List[Dict]:
    url = PROF_SEARCH.format(sid=school_id)
    driver.get(url)
    try:
        w8(driver, lambda d: d.find_elements(By.CSS_SELECTOR, "a[href^='/professor/']") or
                             d.find_elements(By.CSS_SELECTOR, "[data-testid='search-results-header']"), timeout=20)
    except:
        return []

    cards = driver.find_elements(By.CSS_SELECTOR, "a[href^='/professor/']")
    profs = []

    for a in cards[:limit]:
        href = a.get_attribute("href") or ""
        prof_id = href.rstrip("/").split("/")[-1]
        if not prof_id.isdigit() and "/professor/" in href:
            prof_id = href.split("/professor/")[-1].split("/")[0]

        name = extract_text_safe(a, [
            (By.CSS_SELECTOR, "[class*='CardName__StyledCardName']"),
            (By.CSS_SELECTOR, ".CardName__StyledCardName-sc-1gyrgim-0"),
        ])
        dept = extract_text_safe(a, [
            (By.CSS_SELECTOR, "[class*='CardSchool__Department']"),
            (By.XPATH, ".//*[contains(@class,'CardSchool__Department')]"),
        ])
        quality = extract_text_safe(a, [
            (By.CSS_SELECTOR, "[class*='CardNumRating__CardNumRatingNumber']"),
        ])
        ratings_text = extract_text_safe(a, [
            (By.XPATH, ".//*[contains(text(),'rating')] | .//*[contains(text(),'ratings')]"),
        ])
        difficulty = extract_text_safe(a, [
            (By.XPATH, ".//*[contains(text(),'level of difficulty') or contains(text(),'Difficulty')]/preceding-sibling::*[1]"),
        ])

        # 이름 정제 (Dr./Prof. 제거)
        if name:
            name = re.sub(r"^(Dr\.?|Prof\.?)\s+", "", name, flags=re.I).strip()

        profs.append({
            "rmp_prof_id": prof_id,
            "rmp_prof_url": href,
            "name": name,
            "department": dept,
            "rmp_quality": quality,
            "rmp_num_ratings_text": ratings_text,
            "rmp_difficulty": difficulty,
        })

    return profs


# ---------------------- Scholar (Author + 일반 검색) ----------------------
from urllib.parse import quote_plus

def find_scholar_profile_url(driver, prof_name: str, school_kw: str) -> Optional[str]:
    """1) 저자 검색(Author) → 2) 일반 검색 두 경로 모두 시도해서 /citations?user=... URL 반환"""
    q = quote_plus(f"{prof_name} {school_kw}")

    # ------ 1차: Author Search ------
    author_url = f"https://scholar.google.com/citations?view_op=search_authors&hl=en&mauthors={q}&inst=all&oi=drw"
    driver.get(author_url)
    time.sleep(1.2)
    accept_scholar_consent(driver)
    time.sleep(0.8)

    cards = driver.find_elements(By.CSS_SELECTOR, "div.gs_ai_t")
    if cards:
        # affiliation에 school_kw 포함된 카드 우선
        chosen = None
        for c in cards:
            try:
                aff = c.find_element(By.CSS_SELECTOR, "div.gs_ai_aff").text.lower()
            except:
                aff = ""
            if school_kw.lower() in aff:
                chosen = c
                break
        if chosen is None:
            chosen = cards[0]

        try:
            a = chosen.find_element(By.CSS_SELECTOR, "a.gs_ai_name")
            href = a.get_attribute("href") or ""
            if href.startswith("/citations?"):
                return "https://scholar.google.com" + href
            if href.startswith("http"):
                return href
        except:
            pass  # 2차로 진행

    # ------ 2차: 일반 Scholar Search ------
    search_url = f"https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&q={q}"
    driver.get(search_url)
    time.sleep(1.2)
    accept_scholar_consent(driver)
    time.sleep(0.8)

    # 케이스 A: h4.gs_rt2 내부의 프로필 링크
    links = driver.find_elements(By.XPATH, "//h4[contains(@class,'gs_rt2')]//a[contains(@href,'/citations?user=')]")
    if links:
        href = links[0].get_attribute("href") or ""
        return "https://scholar.google.com" + href if href.startswith("/citations?") else href

    # 케이스 B: "일치하는 사용자 프로필" 블록 아래 표 내부 첫 링크
    try:
        block = driver.find_element(By.XPATH, "//h3[contains(@class,'gs_rt')]/a[contains(@href,'view_op=search_authors')]")
        table_link = driver.find_element(By.XPATH, "(//h3[contains(@class,'gs_rt')]/following::h4[contains(@class,'gs_rt2')]//a[contains(@href,'/citations?user=')])[1]")
        href = table_link.get_attribute("href") or ""
        return "https://scholar.google.com" + href if href.startswith("/citations?") else href
    except:
        pass

    # 케이스 C: 안전망 - 페이지 어디든 첫 /citations?user= 링크
    try:
        any_link = driver.find_element(By.XPATH, "//a[contains(@href,'/citations?user=')]")
        href = any_link.get_attribute("href") or ""
        return "https://scholar.google.com" + href if href.startswith("/citations?") else href
    except:
        return None


def parse_scholar_profile_with_driver(driver, profile_url: str) -> Dict:
    """동일 드라이버에서 프로필 상세 파싱"""
    if not profile_url:
        return {}
    driver.get(profile_url)
    time.sleep(random.uniform(1.2, 2.2))
    accept_scholar_consent(driver)
    time.sleep(0.8)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    name_tag = soup.select_one("#gsc_prf_in")
    img_tag  = soup.select_one("#gsc_prf_pup-img")
    aff_tag  = soup.select_one("#gsc_prf_i .gsc_prf_il")
    email_tag = soup.select_one("#gsc_prf_ivh")  # e.g., "Verified email at harvard.edu"

    scholar_name = name_tag.get_text(strip=True) if name_tag else None
    image_url    = img_tag["src"] if img_tag and img_tag.has_attr("src") else None
    affiliation  = aff_tag.get_text(strip=True) if aff_tag else None
    email_verified = email_tag.get_text(strip=True) if email_tag else None

    # 키워드
    keywords = [a.get_text(strip=True) for a in soup.select("#gsc_prf_int a")]

    # 상위 논문 3개
    papers = []
    for row in soup.select("tr.gsc_a_tr")[:3]:
        a = row.select_one("a.gsc_a_at")
        if a and a.has_attr("href"):
            title = a.get_text(strip=True)
            link = BASE_SCHOLAR + a["href"]
            papers.append(f"{title} ({link})")

    # 우측 통계(총 인용)
    citations_total = None
    try:
        stats = soup.select("table.gsc_rsb_st td.gsc_rsb_std")
        if stats and len(stats) >= 1:
            citations_total = stats[0].get_text(strip=True)
    except:
        pass

    return {
        "scholar_profile_url": profile_url,
        "scholar_name": scholar_name,
        "scholar_image_url": image_url,
        "scholar_affiliation": affiliation,
        "scholar_email_verified": email_verified,
        "scholar_keywords": "; ".join(keywords) if keywords else None,
        "scholar_top_papers": "; ".join(papers) if papers else None,
        "scholar_citations_total": citations_total,
    }


# ---------------------- 실행 ----------------------
def main():
    driver = build_driver(headless=False)  # 차단 회피를 위해 우선 False 권장
    try:
        print(f"[1] 학교 검색: {SEARCH_KEYWORD}")
        sid = get_first_school_id(driver, SEARCH_KEYWORD)
        if not sid:
            print("❌ 학교 ID 탐색 실패")
            return
        print(f" - school_id: {sid}")

        print(f"[2] RMP 교수 목록 수집 (최대 {MAX_PROFS}명)")
        rmp_list = collect_professors(driver, sid, MAX_PROFS)
        print(f" - RMP 수집: {len(rmp_list)}명")

        merged = []
        for i, p in enumerate(rmp_list, 1):
            nm = (p.get("name") or "").strip()
            print(f"[{i:02d}/{len(rmp_list)}] {nm} → Scholar 검색...", end=" ", flush=True)

            # Scholar 저자/일반 검색 2단계
            prof_url = find_scholar_profile_url(driver, nm, SEARCH_KEYWORD)
            time.sleep(random.uniform(1.0, 1.8))

            if not prof_url:
                print("없음")
                merged.append({**p, **{
                    "scholar_profile_url": None,
                    "scholar_name": None,
                    "scholar_image_url": None,
                    "scholar_affiliation": None,
                    "scholar_email_verified": None,
                    "scholar_keywords": None,
                    "scholar_top_papers": None,
                    "scholar_citations_total": None,
                }})
                continue

            # 프로필 상세 파싱
            info = parse_scholar_profile_with_driver(driver, prof_url)
            merged.append({**p, **info})
            print("완료")
            time.sleep(random.uniform(1.0, 1.8))

        # CSV 저장
        df = pd.DataFrame(merged)
        out_name = f"merged_rmp_scholar_{SEARCH_KEYWORD}.csv"
        df.to_csv(out_name, index=False, encoding="utf-8-sig")
        print(f"\n✅ 저장 완료: {out_name}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
