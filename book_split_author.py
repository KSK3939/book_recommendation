import pandas as pd
import re

# 파일 경로
ORIGINAL_PATH = './data/final_merge.csv'
PREPROCESSED_PATH = './data/final_merge_preprocessed.csv'
OUTPUT_PATH = './data/final_merge_preprocessed_writer.csv'

# 원본 데이터
df_origin = pd.read_csv(ORIGINAL_PATH, encoding='utf-8-sig')

# 전처리된 데이터
df_pre = pd.read_csv(PREPROCESSED_PATH, encoding='utf-8-sig')


# =========================
# 작가 추출 함수
# =========================
def extract_writer(author):
    if pd.isna(author):
        return ''

    author = str(author)

    # / 앞부분만 사용
    # 예: "히가시노 게이고 저/양윤옥 역" -> "히가시노 게이고 저"
    author = author.split('/')[0]

    # 저, 역 제거
    author = author.replace('저', ' ')
    author = author.replace('역', ' ')

    # 공백 정리
    author = re.sub(r'\s+', ' ', author).strip()

    return author


# =========================
# final_merge에서 작가 컬럼 생성
# =========================
df_origin['작가'] = df_origin['저자'].apply(extract_writer)


# =========================
# ISBN 기준으로 final_merge_preprocessed에 작가 붙이기
# =========================
df_writer = df_origin[['ISBN', '작가']].drop_duplicates(subset=['ISBN'])

df_pre = df_pre.merge(df_writer, on='ISBN', how='left')


# =========================
# 작가 컬럼 위치 조정
# 저자 뒤에 작가를 넣는 방식
# =========================
cols = list(df_pre.columns)

cols.remove('작가')

writer_idx = cols.index('저자') + 1
cols.insert(writer_idx, '작가')

df_pre = df_pre[cols]


# =========================
# 저장
# =========================
df_pre.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')

print(df_pre[['제목', '저자', '작가']].head(20))
print(df_pre.info())