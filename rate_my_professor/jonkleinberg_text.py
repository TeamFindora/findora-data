from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

# 교수 ID (예: Jon Kleinberg)
professor_id = "136263"
url = f"https://www.ratemyprofessors.com/professor/{professor_id}"

# 크롬 옵션 설정
options = Options()
options.add_argument("--headless")  # 브라우저 안 띄우고 실행 (원하면 제거 가능)
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# 드라이버 경로 (예: 현재 폴더에 chromedriver.exe 있으면 생략 가능)
driver = webdriver.Chrome(options=options)

# 페이지 열기
driver.get(url)
time.sleep(3)  # JS 로딩 대기

# 평균 평점
try:
    avg_rating = driver.find_element(By.CLASS_NAME, "RatingValue__Numerator-qw8sqy-2").text
except:
    avg_rating = "N/A"

print(f"📊 평균 평점: {avg_rating}")

# 평점 분포
print("📈 평점 분포:")
dist_labels = driver.find_elements(By.CLASS_NAME, "RatingDistributionChart__LabelText-o2y7ff-6")
dist_values = driver.find_elements(By.CLASS_NAME, "RatingDistributionChart__LabelValue-o2y7ff-7")

for label, value in zip(dist_labels, dist_values):
    print(f"- {label.text}: {value.text}")

# 최근 5개 댓글
print("\n🗣 최근 5개 평가:")

ratings = driver.find_elements(By.CLASS_NAME, "Rating__StyledRating-sc-1rhvpxz-1")[:5]

for i, r in enumerate(ratings, start=1):
    try:
        quality = r.find_element(By.XPATH, './/div[contains(text(), "Quality")]/following-sibling::div').text
        difficulty = r.find_element(By.XPATH, './/div[contains(text(), "Difficulty")]/following-sibling::div').text
        comment = r.find_element(By.CLASS_NAME, "Comments__StyledComments-dzzyvm-0").text
    except:
        quality, difficulty, comment = "N/A", "N/A", "N/A"

    print(f"\n{i}. 📌 Quality: {quality} | 🔧 Difficulty: {difficulty}\n💬 {comment}")

driver.quit()
