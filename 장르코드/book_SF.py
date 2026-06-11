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
DOWNLOAD_DIR = os.path.join(BASE_DIR, "../data")

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

FINAL_CSV_PATH = os.path.join(DOWNLOAD_DIR, "yes24_steadyseller_SF.csv")

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
driver.get("https://www.yes24.com/product/category/steadyseller?pageNumber=1&pageSize=120&categoryNumber=001001046011005")
driver.implicitly_wait(4)

# [120개씩 보기 변경]
try:
    pg_size_option = WebDriverWait(driver, 8).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="pg_size"]/option[4]'))
    )
    pg_size_option.click()
    print("[성공] 120개씩 보기 변경 완료!")
    time.sleep(3.5)
except Exception as e:
    print(f"[오류] 보기 변경 실패 (상세 내용: {e}) -> 기본 설정을 사용합니다.")


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
        print(f"   [Pandas] 제 {current_page}페이지 데이터 추출 성공 ({len(new_df)}개)")

        if os.path.exists(target_csv_path):
            existing_df = pd.read_csv(target_csv_path, encoding='utf-8')
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined_df = new_df

        combined_df.drop_duplicates(inplace=True)
        combined_df.to_csv(target_csv_path, index=False, encoding='utf-8-sig')
        print(f"   [Pandas] 누적 병합 완료: 총 {len(combined_df)}개 데이터 저장됨")

        os.remove(downloaded_excel_path)
    except Exception as e:
        print(f"   [-] 데이터 병합 중 에러 발생: {e}")


# ==========================================
# 크롤링 반복 실행 (1페이지 ~ 4페이지)
# ==========================================
page_index = 1
total_pages = 4

while page_index <= total_pages:
    print("\n" + "=" * 50)
    print(f" 현재 페이지 수집: {page_index}페이지")
    print("=" * 50)

    # 화면에 로딩창이 사라질 때까지 대기 (최대 10초)
    try:
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "yesComLoading"))
        )
    except:
        pass  # 로딩창이 없는 상태면 바로 패스

    # 페이지 상태나 개수에 따라 달라지는 엑셀 다운로드 버튼 XPath 매칭 리스트
    excel_xpaths = [
        '//*[@id="bestContentsWrap"]/div[3]/div[2]/a[5]/span/em',  # 120개 선택 시 위치
        '//*[@id="bestContentsWrap"]/div[4]/div[2]/a[5]/span/em',  # 일반 출력 시 위치
        '//a[contains(@onclick, "downloadExcel")]',                # 함수명 매칭 백업
        '//span[text()="엑셀 다운로드"]/..'                         # 텍스트 기준 백업
    ]

    excel_btn = None
    for xpath in excel_xpaths:
        try:
            # 깨져 있던 By.? 부분을 By.XPATH로 정상 수정
            target_element = driver.find_element(By.XPATH, xpath)
            if target_element.is_displayed():
                excel_btn = target_element
                break
        except:
            continue

    try:
        if excel_btn is None:
            raise Exception("엑셀 다운로드 버튼을 찾을 수 없습니다.")

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", excel_btn)
        time.sleep(0.5)

        # 일반 click()이 아닌 JavaScript 기반 클릭으로 로딩창 간섭 우회
        driver.execute_script("arguments[0].click();", excel_btn)
        print("   [1] 엑셀 다운로드 버튼 클릭 완료")

        latest_file = wait_for_excel_download(DOWNLOAD_DIR)
        if latest_file:
            append_excel_to_csv(latest_file, FINAL_CSV_PATH, page_index)
        else:
            print(f"   [-] [경고] {page_index}페이지 엑셀 파일 다운로드 시간 초과")

    except Exception as e:
        print(f"   [-] 엑셀 다운로드 중 에러: {e}")

    # 다음 페이지로 이동 처리
    if page_index <= total_pages:  # 4페이지가 마지막이면 이동 생략
        try:
            # 로딩창이 완전히 닫혔는지 다시 확인
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located((By.ID, "yesComLoading"))
            )

            # 페이지 번호 링크 매칭
            next_page_xpath = f'//*[@id="bestContentsWrap"]/div[5]/div/div/div/a[{page_index}]'
            next_page_btn = driver.find_element(By.XPATH, next_page_xpath)

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_page_btn)
            time.sleep(0.5)

            # 페이지 번호 클릭도 JavaScript로 안전하게 처리
            driver.execute_script("arguments[0].click();", next_page_btn)
            print(f"   [2] {page_index + 1}페이지로 이동 중... 4.5초 대기")
            time.sleep(4.5)
        except Exception as e:
            print(f"   [-] 페이지 이동 중 에러 발생: {e}")
            break

    page_index += 1

time.sleep(2.0)
driver.quit()

print("\n" + "=" * 50)
print(f" 모든 작업 완료!")
print(f" 최종 결과 파일: {FINAL_CSV_PATH}")
print("=" * 50)