import pandas as pd
from gensim.models import Word2Vec

df_book = pd.read_csv('data/final_merge_preprocessed.csv')
df_book.info()

use_cols = ['설명', '장르', '상품명', '저자', '출판사', '국가']
for col in use_cols:
    df_book[col] = df_book[col].fillna('').astype(str)

def make_word2vec_model(df,columns, save_name):
    sentences = df[columns].agg(' '.join, axis = 1)
    tokens = []
    for sentence in sentences:
        token = sentence.split()
        tokens.append(token)

    embedding_model = Word2Vec(tokens, vector_size = 100, window = 4, min_count = 10, workers = 4, epochs = 100, sg = 1)
    embedding_model.save(f'./models/word2vec_book_{save_name}.model')
    print(list(embedding_model.wv.index_to_key))
    print(len(embedding_model.wv.index_to_key))

    return embedding_model

model_explain = make_word2vec_model(
    df_book,
    ['설명'],
    'explain'
)

model_explain_genre = make_word2vec_model(
    df_book,
    ['설명', '장르'],
    'explain_genre'
)

model_explain_genre_title = make_word2vec_model(
    df_book,
    ['설명', '장르', '상품명'],
    'explain_genre_title'
)

model_explain_genre_title_author = make_word2vec_model(
    df_book,
    ['설명', '장르', '상품명', '저자', '출판사'],
    'explain_genre_title_author'
)

model_total = make_word2vec_model(
    df_book,
    ['설명', '장르', '상품명', '저자', '출판사', '국가'],
    'total'
)