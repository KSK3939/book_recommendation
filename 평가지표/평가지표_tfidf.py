import os
import numpy as np
import pandas as pd
from scipy.io import mmread
from sklearn.metrics.pairwise import linear_kernel
import warnings
warnings.filterwarnings("ignore")

df = pd.read_csv('./data/final_merge_preprocessed.csv')
stages = [
    {"name": "단계 1 (설명만)",     "mtx": "./models/Tfidf_book_explain.mtx"},
    {"name": "단계 2 (+장르)",       "mtx": "./models/Tfidf_book_explain_genre.mtx"},
    {"name": "단계 3 (+제목)",       "mtx": "./models/Tfidf_book_explain_genre_title.mtx"},
    {"name": "단계 4 (+저자)",       "mtx": "./models/Tfidf_book_explain_genre_title_author.mtx"},
    {"name": "전체 융합 (Total)",    "mtx": "./models/Tfidf_book_total.mtx"},
]

SAMPLE_SIZE = 100
K = 10
SEED = 42

def load_matrix(path):
    return mmread(path).tocsr()

# ==========================================
# 지표 1. Precision@10
# 모델 간 차이가 명확히 나고 (20~23.9%)
# 추천 품질의 핵심 지표
# ==========================================
def eval_precision(matrix):
    sample_idx = df.sample(n=SAMPLE_SIZE, random_state=SEED).index
    scores = []
    for ref in sample_idx:
        sims = linear_kernel(matrix[ref], matrix).flatten()
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
# 지표 2. MRR (Mean Reciprocal Rank)
# 모델 간 차이가 명확히 나고 (0.439~0.472)
# 첫 번째 추천의 질을 측정
# ==========================================
def eval_mrr(matrix):
    sample_idx = df.sample(n=SAMPLE_SIZE, random_state=SEED).index
    scores = []
    for ref in sample_idx:
        sims = linear_kernel(matrix[ref], matrix).flatten()
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
# 모델 간 차이가 있고 (0.823~0.845)
# 추천 목록 내 다양성 측정 — Precision과 반대 방향이라 트레이드오프 확인용
# ==========================================
def eval_ild(matrix):
    sample_idx = df.sample(n=SAMPLE_SIZE, random_state=SEED).index
    scores = []
    for ref in sample_idx:
        sims = linear_kernel(matrix[ref], matrix).flatten()
        top = [i for i in np.argsort(sims)[::-1] if i != ref][:K]
        rec = matrix[top]
        pair_sims = linear_kernel(rec, rec)
        np.fill_diagonal(pair_sims, 0)
        n = len(top)
        if n > 1:
            scores.append(1 - pair_sims.sum() / (n * (n - 1)))
    return np.mean(scores)

# ==========================================
# 지표 4. Top-3 Similarity
# 임베딩 밀집도 측정
# ILD와 반대 방향 — 두 지표가 함께 모델의 정밀도/다양성 균형을 설명
# ==========================================
def eval_top3_sim(matrix):
    sample_idx = df.sample(n=SAMPLE_SIZE, random_state=SEED).index
    scores = []
    for ref in sample_idx:
        sims = linear_kernel(matrix[ref], matrix).flatten()
        top3 = [i for i in np.argsort(sims)[::-1] if i != ref][:3]
        scores.extend(sims[top3])
    return np.mean(scores)

# ==========================================
# 지표 5. Rank Stability (Jaccard)
# 모델 간 차이가 있고 (0.29~0.35)
# 비슷한 책을 쿼리할 때 추천이 일관되는지 — 신뢰성 지표
# ==========================================
def eval_stability(matrix):
    sample_idx = df.sample(n=50, random_state=SEED).index
    scores = []
    for ref in sample_idx:
        sims = linear_kernel(matrix[ref], matrix).flatten()
        top = [i for i in np.argsort(sims)[::-1] if i != ref]
        if not top:
            continue
        top_ref = set(top[:K])
        neighbor = top[0]
        sims2 = linear_kernel(matrix[neighbor], matrix).flatten()
        top_nb = set([i for i in np.argsort(sims2)[::-1] if i != neighbor][:K])
        scores.append(len(top_ref & top_nb) / len(top_ref | top_nb))
    return np.mean(scores)

# ==========================================
# 실행
# ==========================================
results = []

print("\n" + "=" * 75)
print("   📊 최종 모델 평가 (의미있는 5개 지표)")
print("=" * 75)
print(f"{'모델':<22} {'Precision@10':>13} {'MRR':>8} {'ILD':>8} {'Top3-Sim':>10} {'Stability':>10}")
print("-" * 75)

for stage in stages:
    if not os.path.exists(stage["mtx"]):
        print(f"  ⚠️  파일 없음: {stage['mtx']}")
        continue

    mat = load_matrix(stage["mtx"])
    row = {
        "모델":           stage["name"],
        "Precision@10":  round(eval_precision(mat), 2),
        "MRR":           round(eval_mrr(mat), 4),
        "ILD":           round(eval_ild(mat), 4),
        "Top3-Sim":      round(eval_top3_sim(mat), 4),
        "Stability":     round(eval_stability(mat), 4),
    }
    results.append(row)
    print(f"{row['모델']:<22} {row['Precision@10']:>12}% {row['MRR']:>8} {row['ILD']:>8} {row['Top3-Sim']:>10} {row['Stability']:>10}")

# ==========================================
# 종합 점수 및 1등 선정
# 가중치 근거:
#   Precision + MRR  → 추천 정확도 (핵심) : 각 35%
#   ILD              → 다양성 (Precision과 트레이드오프) : 15%
#   Top3-Sim         → 임베딩 정밀도 : 10%
#   Stability        → 신뢰성 : 5%
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

    rdf.to_csv("./평가지표/model_evaluation_tfidf.csv", index=False, encoding="utf-8-sig")
    print("  📁 결과 저장: ./평가지표/model_evaluation_tfidf.csv\n")