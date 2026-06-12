import pandas as pd
from konlpy.tag import Okt
import re

# 파일 경로
INPUT_PATH = './data/final_merge.csv'
OUTPUT_PATH = './data/final_merge_preprocessed.csv'

# 데이터 불러오기
df = pd.read_csv(INPUT_PATH, encoding='utf-8-sig')
df.info()

okt = Okt()

df_stopwords = pd.read_csv('data/stopwords.csv')
stopwords = df_stopwords['stopword'].tolist()

# =========================
# 상품명 원본 보존
# =========================
df['제목'] = df['상품명']


# =========================
# 형태소 토큰화 함수
# =========================
def tokenize_text(text):

    text = str(text)

    # 한글, 영어, 숫자만 남김
    text = re.sub('[^가-힣a-zA-Z0-9]', ' ', text)

    # 형태소 분석
    tokened_text = okt.pos(text, stem=True)

    df_token = pd.DataFrame(tokened_text, columns=['word', 'class'])

    # 사용할 품사 선택
    df_token = df_token[
        (df_token['class'] == 'Noun') |
        (df_token['class'] == 'Verb') |
        (df_token['class'] == 'Adjective') |
        (df_token['class'] == 'Alpha') |
        (df_token['class'] == 'Number')
    ]

    words = []

    for word in df_token['word']:
        if word not in stopwords:
            words.append(word)

    return ' '.join(words)

def tokenize_title(text):

    text = str(text)

    # 한글, 영어, 숫자만 남김
    text = re.sub('[^가-힣a-zA-Z0-9]', ' ', text)

    # 형태소 분석
    tokened_text = okt.pos(text, stem=True)

    df_token = pd.DataFrame(tokened_text, columns=['word', 'class'])

    # 사용할 품사 선택
    df_token = df_token[
        (df_token['class'] == 'Noun') |
        (df_token['class'] == 'Verb') |
        (df_token['class'] == 'Adjective') |
        (df_token['class'] == 'Alpha') |
        (df_token['class'] == 'Number')
    ]

    words = []

    for word in df_token['word']:
        words.append(word)

    return ' '.join(words)

# =========================
# 저자 전처리 함수
# =========================
def tokenize_author(author):
    if pd.isna(author):
        return ''

    author = str(author)

    # / 제거
    author = author.replace('/', ' ')

    # 띄어쓰기 기준 분리
    words = author.split()

    # 저, 역 제거
    words = [word for word in words if word not in ['저', '역']]

    return ' '.join(words)


# =========================
# 장르 전처리 함수
# =========================
def tokenize_genre(genre):
    if pd.isna(genre):
        return ''

    genre = str(genre)

    # , 기준 분리
    words = genre.split(',')
    words = [word.strip() for word in words if word.strip()]

    return ' '.join(words)


# =========================
# 컬럼별 전처리 적용
# =========================
df['상품명'] = df['상품명'].apply(tokenize_title)
df['저자'] = df['저자'].apply(tokenize_author)
df['장르'] = df['장르'].apply(tokenize_genre)
df['설명'] = df['설명'].apply(tokenize_text)

# =========================
# 컬럼 순서 정리
# =========================
df = df[
    [
        'ISBN',
        '제목',
        '상품명',
        '저자',
        '출판사',
        '설명',
        '국가',
        '장르'
    ]
]

df = df[df['제목'] != '파닥파닥']
df.drop_duplicates(subset=['제목'], keep='first', inplace=True)

# 기존 index 컬럼이 있으면 제거
if 'index' in df.columns:
    df.drop(columns=['index'], inplace=True)

df.reset_index(drop=True, inplace=True)

# 1부터 시작하는 index 컬럼 추가
df['index'] = range(1, len(df) + 1)

cols = ['index'] + [col for col in df.columns if col != 'index']
df = df[cols]

# =========================
# 저장
# =========================
df.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')

df.info()
print(df.head())