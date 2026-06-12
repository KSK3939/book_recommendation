import os
import numpy as np
import pandas as pd
from gensim.models import Word2Vec
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings("ignore")

df = pd.read_csv('./data/final_merge_preprocessed.csv')

stages = [
    {"name": "단계 1 (설명만)",     "model": "./models/word2vec_book_explain.model"},
    {"name": "단계 2 (+장르)",       "model": "./models/word2vec_book_explain_genre.model"},
    {"name": "단계 3 (+제목)",       "model": "./models/word2vec_book_explain_genre_title.model"},
    {"name": "단계 4 (+저자)",       "model": "./models/word2vec_book_explain_genre_title_author.model"},
    {"name": "전체 융합 (Total)",    "model": "./models/word2vec_book_total.model"},
]

SAMPLE_SIZE = 100
K = 10
SEED = 42

# ==========================================
# 책 벡터 생성 (단어 벡터 평균)
# ==========================================
def get_book_vectors(w2v_model, texts):
    vectors = []
    for text in texts:
        if not isinstance(text, str):
            text = ""
        words = text.split()
        valid = [w2v_model.wv[w] for w in words if w in w2v_model.wv]
        if valid:
            vectors.append(np.mean(valid, axis=0))
        else:
            vectors.append(np.zeros(w2v_model.vector_size))
    return np.array(vectors)

# ==========================================
# 텍스트 컬럼 자동 감지 및 결합
# ==========================================
def get_text_column(stage_name):
    # 단계별로 사용하는 컬럼을 추론 (컬럼명은 실제 df에 맞게 수정)
    text_cols = []
    col_names = df.columns.tolist()

    # 설명 컬럼 (항상 포함)
    for c in col_names:
        if any(k in c for k in ['설명', 'explain', 'description', 'intro', 'content']):
            text_cols.append(c)
            break

    if '장르' in stage_name or '제목' in stage_name or '저자' in stage_name or 'Total' in stage_name:
        for c in col_names:
            if any(k in c for k in ['장르', 'genre', 'category']):
                text_cols.append(c)
                break

    if '제목' in stage_name or '저자' in stage_name or 'Total' in stage_name:
        for c in col_names:
            if any(k in c for k in ['제목', 'title', 'name']):
                text_cols.append(c)
                break

    if '저자' in stage_name or 'Total' in stage_name:
        for c in col_names:
            if any(k in c for k in ['저자', 'author', 'writer']):
                text_cols.append(c)
                break

    if not text_cols:
        # 자동 감지 실패 시 첫 번째 문자열 컬럼 사용
        text_cols = [col_names[0]]

    combined = df[text_cols].fillna("").astype(str).agg(" ".join, axis=1)
    return combined


# ==========================================
# 지표 1. Precision@K
# ==========================================
def eval_precision(book_vecs):
    sample_idx = df.sample(n=SAMPLE_SIZE, random_state=SEED).index
    scores = []
    for ref in sample_idx:
        sims = cosine_similarity([book_vecs[ref]], book_vecs).flatten()
        top = [i for i in np.argsort(sims)[::-1] if i != ref][:K]
        tgt_genre  = df.iloc[ref, 3] if df.shape[1] > 3 else ""
        tgt_author = df.iloc[ref, 4] if df.shape[1] > 4 else ""
        matched = sum(
            1 for i in top
            if df.iloc[i, 3] == tgt_genre or df.iloc[i, 4] == tgt_author
        )
        scores.append(matched / K)
    return np.mean(scores) * 100


# ==========================================
# 지표 2. MRR
# ==========================================
def eval_mrr(book_vecs):
    sample_idx = df.sample(n=SAMPLE_SIZE, random_state=SEED).index
    scores = []
    for ref in sample_idx:
        sims = cosine_similarity([book_vecs[ref]], book_vecs).flatten()
        top = [i for i in np.argsort(sims)[::-1] if i != ref][:K]
        tgt_genre  = df.iloc[ref, 3] if df.shape[1] > 3 else ""
        tgt_author = df.iloc[ref, 4] if df.shape[1] > 4 else ""
        first_rank = next(
            (rank for rank, i in enumerate(top, 1)
             if df.iloc[i, 3] == tgt_genre or df.iloc[i, 4] == tgt_author),
            0
        )
        scores.append(1.0 / first_rank if first_rank else 0.0)
    return np.mean(scores)


# ==========================================
# 지표 3. ILD (Intra-List Diversity)
# ==========================================
def eval_ild(book_vecs):
    sample_idx = df.sample(n=SAMPLE_SIZE, random_state=SEED).index
    scores = []
    for ref in sample_idx:
        sims = cosine_similarity([book_vecs[ref]], book_vecs).flatten()
        top = [i for i in np.argsort(sims)[::-1] if i != ref][:K]
        rec_vecs = book_vecs[top]
        pair_sims = cosine_similarity(rec_vecs, rec_vecs)
        np.fill_diagonal(pair_sims, 0)
        n = len(top)
        if n > 1:
            scores.append(1 - pair_sims.sum() / (n * (n - 1)))
    return np.mean(scores)


# ==========================================
# 지표 4. Top-3 Similarity
# ==========================================
def eval_top3_sim(book_vecs):
    sample_idx = df.sample(n=SAMPLE_SIZE, random_state=SEED).index
    scores = []
    for ref in sample_idx:
        sims = cosine_similarity([book_vecs[ref]], book_vecs).flatten()
        top3 = [i for i in np.argsort(sims)[::-1] if i != ref][:3]
        scores.extend(sims[top3])
    return np.mean(scores)


# ==========================================
# 지표 5. Rank Stability (Jaccard)
# ==========================================
def eval_stability(book_vecs):
    sample_idx = df.sample(n=50, random_state=SEED).index
    scores = []
    for ref in sample_idx:
        sims = cosine_similarity([book_vecs[ref]], book_vecs).flatten()
        top = [i for i in np.argsort(sims)[::-1] if i != ref]
        if not top:
            continue
        top_ref = set(top[:K])
        neighbor = top[0]
        sims2 = cosine_similarity([book_vecs[neighbor]], book_vecs).flatten()
        top_nb = set([i for i in np.argsort(sims2)[::-1] if i != neighbor][:K])
        scores.append(len(top_ref & top_nb) / len(top_ref | top_nb))
    return np.mean(scores)


# ==========================================
# 실행
# ==========================================
results = []

print("\n" + "=" * 75)
print("   📊 Word2Vec 모델 평가 (5개 지표)")
print("=" * 75)
print(f"{'모델':<22} {'Precision@10':>13} {'MRR':>8} {'ILD':>8} {'Top3-Sim':>10} {'Stability':>10}")
print("-" * 75)

for stage in stages:
    path = stage["model"]
    if not os.path.exists(path):
        print(f"  ⚠️  파일 없음: {path}")
        continue

    w2v = Word2Vec.load(path)
    texts = get_text_column(stage["name"])
    book_vecs = get_book_vectors(w2v, texts)

    row = {
        "모델":          stage["name"],
        "Precision@10": round(eval_precision(book_vecs), 2),
        "MRR":          round(eval_mrr(book_vecs), 4),
        "ILD":          round(eval_ild(book_vecs), 4),
        "Top3-Sim":     round(eval_top3_sim(book_vecs), 4),
        "Stability":    round(eval_stability(book_vecs), 4),
    }
    results.append(row)
    print(f"{row['모델']:<22} {row['Precision@10']:>12}% {row['MRR']:>8} {row['ILD']:>8} {row['Top3-Sim']:>10} {row['Stability']:>10}")

# ==========================================
# 종합 점수 및 1등 선정
# ==========================================
print("\n" + "=" * 75)
print("   🏆 종합 점수 및 최종 1등")
print("   가중치: Precision 35% | MRR 35% | ILD 15% | Top3-Sim 10% | Stability 5%")
print("=" * 75)

if results:
    rdf = pd.DataFrame(results)

    def norm(col):
        mn, mx = col.min(), col.max()
        if mx == mn:
            return pd.Series([0.5] * len(col))
        return (col - mn) / (mx - mn)

    rdf["종합점수"] = (
        norm(rdf["Precision@10"]) * 0.35 +
        norm(rdf["MRR"])          * 0.35 +
        norm(rdf["ILD"])          * 0.15 +
        norm(rdf["Top3-Sim"])     * 0.10 +
        norm(rdf["Stability"])    * 0.05
    ).round(4)

    ranked = rdf.sort_values("종합점수", ascending=False).reset_index(drop=True)
    medals = ["🥇", "🥈", "🥉", " 4위", " 5위"]
    for i, row in ranked.iterrows():
        print(f"  {medals[i]}  {row['모델']:<25} 종합점수: {row['종합점수']:.4f}")

    winner = ranked.iloc[0]
    print("\n" + "=" * 75)
    print(f"  ✅ 최종 1등: {winner['모델']}")
    print(f"     - Precision@10 : {winner['Precision@10']}%")
    print(f"     - MRR          : {winner['MRR']}")
    print(f"     - ILD          : {winner['ILD']}")
    print(f"     - Top3-Sim     : {winner['Top3-Sim']}")
    print(f"     - Stability    : {winner['Stability']}")
    print(f"     - 종합점수     : {winner['종합점수']}")
    print("=" * 75 + "\n")

    rdf.to_csv("./평가지표/model_evaluation_w2v.csv", index=False, encoding="utf-8-sig")
    print("  📁 결과 저장: ./평가지표/model_evaluation_w2v.csv\n")