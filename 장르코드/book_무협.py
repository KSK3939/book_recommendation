
#책권수가 너무 적어서 빼는 것이 나아보임 (아니면 다른 거랑 통합하든)
import os
import glob
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "data")

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

#바꿀부분 명 바꾸기
FINAL_CSV_PATH = os.path.join(DOWNLOAD_DIR, "yes24_steadyseller_무협.csv")

if os.path.exists(FINAL_CSV_PATH):
    os.remove(FINAL_CSV_PATH)

print("-" * 60)
print(f"[*] 최종 파일 저장 경로: {FINAL_CSV_PATH}")
print("-" * 60)

chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")

prefs = {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
chrome_options.add_experimental_option("prefs", prefs)

service = ChromeService(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# [접속] 모아야되는 링크 바꾸기
driver.get("https://www.yes24.com/product/category/steadyseller?pageNumber=1&pageSize=24&categoryNumber=001001046011004")
driver.implicitly_wait(4)


try:
    pg_size_option = WebDriverWait(driver, 8).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="pg_size"]/option[4]'))
    )
    pg_size_option.click()
    print("[성공] 120개씩 보기 변경 완료!")
    time.sleep(3.5)
except Exception as e:
    print(f"[오류] 보기 변경 실패 (기본 설정을 사용합니다): {e}")


def wait_for_excel_download(download_dir, timeout=20):
    start_time = time.time()
    while time.time() - start_time < timeout:
        all_files = os.listdir(download_dir)
        is_downloading = any('.crdownload' in f or '.tmp' in f or '~lock' in f for f in all_files)
        xlsx_files = glob.glob(os.path.join(download_dir, "*.xlsx"))

        if xlsx_files and not is_downloading:
            target_file = max(xlsx_files, key=os.path.getmtime)
            if os.path.getsize(target_file) > 1000:
                return target_file
        time.sleep(0.5)
    return None


def append_excel_to_csv(downloaded_excel_path, target_csv_path, current_page):
    try:
        new_df = pd.read_excel(downloaded_excel_path, engine='openpyxl')
        print(f"   [Pandas] 제 {current_page}페이지 데이터 추출 완료 ({len(new_df)}개)")

        if os.path.exists(target_csv_path):
            existing_df = pd.read_csv(target_csv_path, encoding='utf-8')
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined_df = new_df

        combined_df.drop_duplicates(inplace=True)
        combined_df.to_csv(target_csv_path, index=False, encoding='utf-8-sig')
        print(f"   [Pandas] 현재 누적 병합 데이터: 총 {len(combined_df)}개")

        os.remove(downloaded_excel_path)
    except Exception as e:
        print(f"   [-] 데이터 저장 중 오류 발생: {e}")


# ==========================================
# 크롤링 반복 주행 (1페이지 ~ 7페이지 완주)
# ==========================================
page_index = 1
total_pages = 1 # 120으로 바꾸고 페이지수 체크해서 바꾸기

while page_index <= total_pages:
    print("\n" + "=" * 50)
    print(f" 현재 페이지 수집 중: {page_index}페이지 / 총 {total_pages}페이지")
    print("=" * 50)

    # 에러의 원인이었던 투명 로딩창이 화면에서 완전히 사라질 때까지 대기
    try:
        WebDriverWait(driver, 12).until(
            EC.invisibility_of_element_located((By.ID, "yesComLoading"))
        )
    except:
        pass  # 이미 로딩창이 없다면 대기 없이 통과

    # 유동적인 화면 구조에 맞춰 엑셀 다운로드 버튼을 찾는 XPath 후보군
    excel_xpaths = [
        '//*[@id="bestContentsWrap"]/div[3]/div[2]/a[5]/span/em',
        '//*[@id="bestContentsWrap"]/div[4]/div[2]/a[5]/span/em',
        '//a[contains(@onclick, "downloadExcel")]'
    ]

    excel_btn = None
    for xpath in excel_xpaths:
        try:
            excel_btn = driver.find_element(By.XPATH, xpath)
            if excel_btn.is_displayed():
                break
        except:
            continue

    try:
        if excel_btn is None:
            raise Exception("엑셀 다운로드 버튼의 위치를 찾을 수 없습니다.")

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", excel_btn)
        time.sleep(0.5)

        # 로딩창 간섭(Click Intercepted)을 완전히 우회하기 위해 JavaScript 강제 클릭 사용
        driver.execute_script("arguments[0].click();", excel_btn)
        print("   [1] 엑셀 다운로드 버튼 클릭 완료")

        latest_file = wait_for_excel_download(DOWNLOAD_DIR)
        if latest_file:
            append_excel_to_csv(latest_file, FINAL_CSV_PATH, page_index)
        else:
            print(f"   [-] [경고] {page_index}페이지 엑셀 다운로드 시간 초과")

    except Exception as e:
        print(f"   [-] 엑셀 다운로드 단계 실패: {e}")

    # 다음 페이지 번호 클릭 처리
    if page_index < total_pages:
        try:
            # 페이지 넘어가기 전 한 번 더 로딩창 완전 소멸 대기
            WebDriverWait(driver, 12).until(
                EC.invisibility_of_element_located((By.ID, "yesComLoading"))
            )

            # 다음 가야 할 페이지의 '숫자' 자체를 타겟팅하여 인덱스 뒤틀림 방지
            # 예: 4페이지로 가야 할 때는 텍스트가 정확히 '4'인 요소를 찾아서 클릭
            target_page_num = page_index + 1
            next_page_xpath = f'//*[@id="bestContentsWrap"]/div[5]/div/div/div/a[text()="{target_page_num}"]'
            next_page_btn = driver.find_element(By.XPATH, next_page_xpath)

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_page_btn)
            time.sleep(0.5)

            # 페이지 번호 클릭도 방해받지 않게 JS 클릭 처리
            driver.execute_script("arguments[0].click();", next_page_btn)
            print(f"   [2] {target_page_num}페이지로 이동 중... 4.5초 대기")
            time.sleep(4.5)
        except Exception as e:
            print(f"   [-] 페이지 이동 중 오류 발생 (수집 조기 종료됨): {e}")
            break

    page_index += 1

time.sleep(2.0)
driver.quit()

print("\n" + "=" * 50)
print(f" 7페이지 전 권수 수집 완료!")
print(f" 최종 파일 결과: {FINAL_CSV_PATH}")
print("=" * 50)