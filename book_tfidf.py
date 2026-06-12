import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.io import mmwrite, mmread
import pickle

df = pd.read_csv('./data/final_merge_preprocessed.csv')
df.info()

Tfidf = TfidfVectorizer(sublinear_tf = True)
Tfidf_matrix = Tfidf.fit_transform(df.설명)
print(Tfidf_matrix.shape)

with open('./models/tfidf.pkl', 'wb') as f:
    pickle.dump(Tfidf, f)
mmwrite('./models/Tfidf_book_e.mtx', Tfidf_matrix)

# 1. 설명
# 2. 설명 + 장르
# 3. 설명 + 장르 + 제목
# 4. 설명 + 장르 + 제목 + 저자 + 출판사