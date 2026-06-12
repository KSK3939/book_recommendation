import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.io import mmwrite, mmread
import pickle

df = pd.read_csv('./data/final_merge_preprocessed.csv')
df.info()

use_cols = ['설명', '장르', '상품명', '저자', '출판사', '국가']
for col in use_cols:
    df[col] = df[col].fillna('').astype(str)

def make_tfidf_matrix(df, colums, save_name):
    text_data = df[colums].agg(' '.join, axis = 1)
    tfidf = TfidfVectorizer(sublinear_tf = True)
    tfidf_matrix = tfidf.fit_transform(text_data)

    print('{save_name} shape :', tfidf_matrix.shape)

    with open(f'./models/tfidf_{save_name}.pkl', 'wb') as f:
        pickle.dump(tfidf, f)

    mmwrite(f'./models/Tfidf_book_{save_name}.mtx', tfidf_matrix)

    return tfidf, tfidf_matrix

tfidf_explain, matrix_explain = make_tfidf_matrix(df, ['설명'], 'explain')

tfidf_explain_genre, matrix_explain_genre = make_tfidf_matrix(df, ['설명', '장르'], 'explain_genre')
tfidf_explain_genre_title, matrix_explain_genre_title = make_tfidf_matrix(df, ['설명', '장르', '상품명'], 'explain_genre_title')
tfidf_explain_genre_title_author, matrix_explain_genre_title_author = make_tfidf_matrix(df, ['설명', '장르', '상품명', '저자', '출판사'], 'explain_genre_title_author')
tfidf_total, matrix_total = make_tfidf_matrix(df, ['설명', '장르', '상품명', '저자', '출판사', '국가'], 'total')

# 1. 설명
# 2. 설명 + 장르
# 3. 설명 + 장르 + 제목
# 4. 설명 + 장르 + 제목 + 저자 + 출판사
# 4. 설명 + 장르 + 제목 + 저자 + 출판사 + 국가