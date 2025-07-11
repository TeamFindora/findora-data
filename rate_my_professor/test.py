import requests
from bs4 import BeautifulSoup

def get_rmp_professor_id(prof_name):
    search_url = f"https://www.ratemyprofessors.com/search/professors/?q={prof_name.replace(' ', '%20')}"
    headers = {'User-Agent': 'Mozilla/5.0'}

    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 검색 결과에서 첫 번째 교수 카드 링크 추출
    prof_link = soup.find('a', class_='TeacherCard__StyledTeacherCard-syjs0d-0 eerjaA')
    if prof_link:
        href = prof_link['href']  # 예: /professor/136263
        prof_id = href.split('/')[-1]
        return prof_id
    else:
        return None

prof_name = "Jon Kleinberg"
rmp_id = get_rmp_professor_id(prof_name)
print("RMP ID:", rmp_id)