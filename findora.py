import pandas as pd
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def parse_scholar_profile(profile_url):
    if not profile_url:
        return {}

    # 셀레니움 크롬 옵션 설정
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 브라우저 창 안 띄움
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--lang=en')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(profile_url)
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # 이미지 URL
    img_tag = soup.select_one("#gsc_prf_pup-img")
    image_url = img_tag["src"] if img_tag and img_tag.has_attr("src") else None

    # 연구 키워드
    keywords = [tag.text for tag in soup.select("#gsc_prf_int a")]

    # 소속
    aff_tag = soup.select_one("#gsc_prf_i .gsc_prf_il")
    affiliation = aff_tag.text.strip() if aff_tag else None

    # 상위 논문 3개
    papers = []
    for row in soup.select("tr.gsc_a_tr")[:3]:
        title_tag = row.select_one("a.gsc_a_at")
        if title_tag:
            title = title_tag.text
            link = "https://scholar.google.com" + title_tag["href"]
            papers.append(f"{title} ({link})")

    driver.quit()

    return {
        "image_url": image_url,
        "affiliation_from_scholar": affiliation,
        "keywords": "; ".join(keywords),
        "top_papers": "; ".join(papers)
    }

# 🔽 CSV 파일 읽기
df = pd.read_csv("./top_400_with_scholarurl.csv")  

# 🔄 scholar profile_url 기반 크롤링
results = []
for i, row in df.iterrows():
    print(f"{i+1}/{len(df)}: {row['name']}...", end=" ")
    url = row.get("profile_url", "")
    if pd.isna(url) or url.strip() == "":
        print("❌ No profile_url")
        continue
    info = parse_scholar_profile(url)
    combined = {**row.to_dict(), **info}
    results.append(combined)
    print("✅ Done")
    time.sleep(1.5)

# 💾 CSV로 저장
output_df = pd.DataFrame(results)
output_df.to_csv("final_scholar_results.csv", index=False)
print("✅ final_scholar_results.csv 저장 완료!")