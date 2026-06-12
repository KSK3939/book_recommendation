import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import matplotlib
matplotlib.rcParams['font.family'] = 'NanumGothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# ==========================================
# 실제 결과값 입력
# ==========================================
stages = ["단계1\n(설명)", "단계2\n(+장르)", "단계3\n(+제목)", "단계4\n(+저자)", "Total"]

# TF-IDF 결과
tfidf = {
    "Precision": [20.0, 19.8, 20.7, 23.7, 23.9],
    "MRR":       [0.4394, 0.439, 0.438, 0.4715, 0.4724],
    "ILD":       [0.8445, 0.8412, 0.836, 0.8279, 0.823],
    "Top3Sim":   [0.3151, 0.316, 0.3183, 0.3334, 0.3357],
    "Stability": [0.2989, 0.2915, 0.3183, 0.331, 0.3456],
}

# Word2Vec 결과 (Total 없음 → NaN)
w2v = {
    "Precision": [14.5, 14.8, 15.2, 17.5, None],
    "MRR":       [0.3128, 0.3186, 0.3442, 0.3784, None],
    "ILD":       [0.1471, 0.1458, 0.1492, 0.1475, None],
    "Top3Sim":   [0.8948, 0.8958, 0.8939, 0.897, None],
    "Stability": [0.2594, 0.2688, 0.2645, 0.2888, None],
}

# 색상
C_TFIDF  = "#185FA5"
C_W2V    = "#D85A30"
C_BEST   = "#1D9E75"
C_GRAY   = "#AAAAAA"
C_BG     = "#F8F9FA"

# None → NaN 변환
def to_arr(lst):
    return np.array([np.nan if v is None else v for v in lst])

# ==========================================
# 1. 막대그래프 — Precision & MRR 나란히
# ==========================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5), facecolor=C_BG)
fig.suptitle("TF-IDF vs Word2Vec — 정확도 비교", fontsize=16, fontweight='bold', y=1.02)

x = np.arange(len(stages))
w = 0.35

for ax, metric, ylabel, title in zip(
    axes,
    ["Precision", "MRR"],
    ["Precision@10 (%)", "MRR"],
    ["Precision@10", "MRR (Mean Reciprocal Rank)"]
):
    t_vals = to_arr(tfidf[metric])
    v_vals = to_arr(w2v[metric])

    bars1 = ax.bar(x - w/2, t_vals, w, label="TF-IDF", color=C_TFIDF, alpha=0.85, zorder=3)
    bars2 = ax.bar(x + w/2, v_vals, w, label="Word2Vec", color=C_W2V, alpha=0.85, zorder=3)

    # 값 레이블
    for bar in bars1:
        h = bar.get_height()
        if not np.isnan(h):
            ax.text(bar.get_x() + bar.get_width()/2, h + 0.002 * ax.get_ylim()[1],
                    f"{h:.2f}", ha='center', va='bottom', fontsize=8.5, color=C_TFIDF, fontweight='bold')
    for bar in bars2:
        h = bar.get_height()
        if not np.isnan(h):
            ax.text(bar.get_x() + bar.get_width()/2, h + 0.002 * ax.get_ylim()[1],
                    f"{h:.2f}", ha='center', va='bottom', fontsize=8.5, color=C_W2V, fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(stages, fontsize=9)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.set_facecolor(C_BG)
    ax.grid(axis='y', alpha=0.3, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig("./chart_01_precision_mrr.png", dpi=150, bbox_inches='tight')
plt.close()
print("✅ chart_01_precision_mrr.png 저장")

# ==========================================
# 2. 꺾은선 — 5개 지표 단계별 변화 (TF-IDF만)
# ==========================================
fig, axes = plt.subplots(1, 3, figsize=(16, 5), facecolor=C_BG)
fig.suptitle("TF-IDF — 피처 추가 단계별 지표 변화", fontsize=16, fontweight='bold', y=1.02)

metrics_line = [
    ("Precision", "Precision@10 (%)", "#185FA5"),
    ("MRR",       "MRR",              "#1D9E75"),
    ("Stability", "Stability (Jaccard)", "#7F77DD"),
]

for ax, (metric, ylabel, color) in zip(axes, metrics_line):
    vals = to_arr(tfidf[metric])
    ax.plot(stages, vals, marker='o', color=color, linewidth=2.5, markersize=8, zorder=3)
    ax.fill_between(stages, vals, alpha=0.12, color=color)
    for i, v in enumerate(vals):
        ax.annotate(f"{v:.4g}", (stages[i], v),
                    textcoords="offset points", xytext=(0, 10),
                    ha='center', fontsize=9, color=color, fontweight='bold')
    # Total 강조
    ax.axvline(x=4, color=C_BEST, linestyle='--', alpha=0.5, linewidth=1.5)
    ax.set_title(ylabel, fontsize=13, fontweight='bold')
    ax.set_facecolor(C_BG)
    ax.grid(alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig("./chart_02_tfidf_trend.png", dpi=150, bbox_inches='tight')
plt.close()
print("✅ chart_02_tfidf_trend.png 저장")

# ==========================================
# 3. 레이더 차트 — TF-IDF Total vs W2V 단계4 비교
# ==========================================
labels = ['Precision', 'MRR', 'ILD\n(다양성)', 'Top3\nSim', 'Stability']
N = len(labels)

# 정규화 (0~1)
def normalize(vals, ref_min, ref_max):
    return [(v - ref_min) / (ref_max - ref_min + 1e-9) for v in vals]

tfidf_total = [23.9, 0.4724, 0.823, 0.3357, 0.3456]
w2v_best    = [17.5, 0.3784, 0.1475, 0.897, 0.2888]

mins = [min(a, b) for a, b in zip(tfidf_total, w2v_best)]
maxs = [max(a, b) for a, b in zip(tfidf_total, w2v_best)]

tfidf_norm = normalize(tfidf_total, min(mins), max(maxs))
w2v_norm   = normalize(w2v_best,   min(mins), max(maxs))

# 각 지표별 개별 정규화
tfidf_norm = [(v - mn) / (mx - mn + 1e-9) for v, mn, mx in zip(tfidf_total, mins, maxs)]
w2v_norm   = [(v - mn) / (mx - mn + 1e-9) for v, mn, mx in zip(w2v_best, mins, maxs)]

angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
angles += angles[:1]
tfidf_norm += tfidf_norm[:1]
w2v_norm   += w2v_norm[:1]

fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True), facecolor=C_BG)
ax.set_facecolor(C_BG)

ax.plot(angles, tfidf_norm, 'o-', linewidth=2.5, color=C_TFIDF, label="TF-IDF (Total)")
ax.fill(angles, tfidf_norm, alpha=0.2, color=C_TFIDF)

ax.plot(angles, w2v_norm, 'o-', linewidth=2.5, color=C_W2V, label="Word2Vec (단계4)")
ax.fill(angles, w2v_norm, alpha=0.15, color=C_W2V)

ax.set_thetagrids(np.degrees(angles[:-1]), labels, fontsize=12)
ax.set_ylim(0, 1)
ax.set_yticks([0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(["25%", "50%", "75%", "100%"], fontsize=8, color='gray')
ax.grid(color='gray', alpha=0.3)
ax.set_title("TF-IDF Total vs Word2Vec 단계4\n지표 프로파일 비교", fontsize=14, fontweight='bold', pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.15), fontsize=11)

plt.tight_layout()
plt.savefig("./chart_03_radar.png", dpi=150, bbox_inches='tight')
plt.close()
print("✅ chart_03_radar.png 저장")

# ==========================================
# 4. 히트맵 — 전 모델 × 전 지표
# ==========================================
import matplotlib.colors as mcolors

model_labels = [
    "TF-IDF 단계1", "TF-IDF 단계2", "TF-IDF 단계3", "TF-IDF 단계4", "TF-IDF Total",
    "W2V 단계1",    "W2V 단계2",    "W2V 단계3",    "W2V 단계4",
]
metric_labels = ["Precision@10", "MRR", "ILD", "Top3-Sim", "Stability"]

raw = np.array([
    [20.0,  0.4394, 0.8445, 0.3151, 0.2989],
    [19.8,  0.4390, 0.8412, 0.3160, 0.2915],
    [20.7,  0.4380, 0.8360, 0.3183, 0.3183],
    [23.7,  0.4715, 0.8279, 0.3334, 0.3310],
    [23.9,  0.4724, 0.8230, 0.3357, 0.3456],
    [14.5,  0.3128, 0.1471, 0.8948, 0.2594],
    [14.8,  0.3186, 0.1458, 0.8958, 0.2688],
    [15.2,  0.3442, 0.1492, 0.8939, 0.2645],
    [17.5,  0.3784, 0.1475, 0.8970, 0.2888],
])

# 컬럼별 정규화
norm_data = np.zeros_like(raw)
for col in range(raw.shape[1]):
    mn, mx = raw[:, col].min(), raw[:, col].max()
    norm_data[:, col] = (raw[:, col] - mn) / (mx - mn + 1e-9)

fig, ax = plt.subplots(figsize=(10, 7), facecolor=C_BG)
im = ax.imshow(norm_data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)

ax.set_xticks(range(len(metric_labels)))
ax.set_xticklabels(metric_labels, fontsize=11, fontweight='bold')
ax.set_yticks(range(len(model_labels)))
ax.set_yticklabels(model_labels, fontsize=10)

# 구분선 (TF-IDF / W2V 경계)
ax.axhline(4.5, color='white', linewidth=3)

# 셀 값 표시
for i in range(len(model_labels)):
    for j in range(len(metric_labels)):
        ax.text(j, i, f"{raw[i, j]:.3f}", ha='center', va='center',
                fontsize=9, color='black', fontweight='bold')

ax.set_title("전체 모델 × 지표 히트맵 (컬럼별 정규화)", fontsize=14, fontweight='bold', pad=15)
plt.colorbar(im, ax=ax, fraction=0.03, pad=0.04, label="상대 점수 (높을수록 좋음)")

# TF-IDF / W2V 레이블
ax.text(-0.7, 2, "TF-IDF", fontsize=12, color=C_TFIDF, fontweight='bold',
        rotation=90, va='center', ha='center')
ax.text(-0.7, 6.5, "W2V", fontsize=12, color=C_W2V, fontweight='bold',
        rotation=90, va='center', ha='center')

plt.tight_layout()
plt.savefig("./chart_04_heatmap.png", dpi=150, bbox_inches='tight')
plt.close()
print("✅ chart_04_heatmap.png 저장")

# ==========================================
# 5. 산점도 — Precision vs MRR (모델별)
# ==========================================
fig, ax = plt.subplots(figsize=(9, 6), facecolor=C_BG)
ax.set_facecolor(C_BG)

tfidf_prec = [20.0, 19.8, 20.7, 23.7, 23.9]
tfidf_mrr  = [0.4394, 0.439, 0.438, 0.4715, 0.4724]
w2v_prec   = [14.5, 14.8, 15.2, 17.5]
w2v_mrr    = [0.3128, 0.3186, 0.3442, 0.3784]
t_labels   = ["단계1", "단계2", "단계3", "단계4", "Total"]
v_labels   = ["단계1", "단계2", "단계3", "단계4"]

# TF-IDF
ax.scatter(tfidf_prec, tfidf_mrr, color=C_TFIDF, s=120, zorder=5, label="TF-IDF")
for i, (x, y, lbl) in enumerate(zip(tfidf_prec, tfidf_mrr, t_labels)):
    offset = (5, 5) if i != 4 else (5, -12)
    ax.annotate(lbl, (x, y), xytext=offset, textcoords='offset points',
                fontsize=9, color=C_TFIDF, fontweight='bold')

# Total 강조
ax.scatter([23.9], [0.4724], color=C_BEST, s=250, zorder=6, marker='*')
ax.annotate("★ TF-IDF Total\n(최종 선택)", (23.9, 0.4724),
            xytext=(8, 8), textcoords='offset points', fontsize=9, color=C_BEST, fontweight='bold')

# Word2Vec
ax.scatter(w2v_prec, w2v_mrr, color=C_W2V, s=120, zorder=5, label="Word2Vec", marker='s')
for x, y, lbl in zip(w2v_prec, w2v_mrr, v_labels):
    ax.annotate(lbl, (x, y), xytext=(5, 5), textcoords='offset points',
                fontsize=9, color=C_W2V, fontweight='bold')

ax.set_xlabel("Precision@10 (%)", fontsize=12)
ax.set_ylabel("MRR", fontsize=12)
ax.set_title("Precision vs MRR 산점도\n오른쪽 위로 갈수록 좋은 모델", fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(alpha=0.3)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# 사분면 구분선
ax.axvline(x=np.mean(tfidf_prec + w2v_prec), color='gray', linestyle='--', alpha=0.4)
ax.axhline(y=np.mean(tfidf_mrr + w2v_mrr), color='gray', linestyle='--', alpha=0.4)

plt.tight_layout()
plt.savefig("./chart_05_scatter.png", dpi=150, bbox_inches='tight')
plt.close()
print("✅ chart_05_scatter.png 저장")

# ==========================================
# 6. 박스 스타일 종합 비교표 (이미지)
# ==========================================
fig, ax = plt.subplots(figsize=(13, 5), facecolor=C_BG)
ax.axis('off')

col_labels = ["모델", "Precision@10", "MRR", "ILD", "Top3-Sim", "Stability", "종합점수"]
rows_data = [
    ["TF-IDF 단계1",  "20.0%", "0.4394", "0.8445", "0.3151", "0.2989", "0.33"],
    ["TF-IDF 단계2",  "19.8%", "0.4390", "0.8412", "0.3160", "0.2915", "0.18"],
    ["TF-IDF 단계3",  "20.7%", "0.4380", "0.8360", "0.3183", "0.3183", "0.28"],
    ["TF-IDF 단계4",  "23.7%", "0.4715", "0.8279", "0.3334", "0.3310", "0.75"],
    ["TF-IDF Total ★","23.9%", "0.4724", "0.8230", "0.3357", "0.3456", "0.73"],
    ["W2V 단계1",     "14.5%", "0.3128", "0.1471", "0.8948", "0.2594", "0.09"],
    ["W2V 단계2",     "14.8%", "0.3186", "0.1458", "0.8958", "0.2688", "0.14"],
    ["W2V 단계3",     "15.2%", "0.3442", "0.1492", "0.8939", "0.2645", "0.41"],
    ["W2V 단계4",     "17.5%", "0.3784", "0.1475", "0.8970", "0.2888", "0.93*"],
]

table = ax.table(
    cellText=rows_data,
    colLabels=col_labels,
    cellLoc='center',
    loc='center',
)
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.2, 1.8)

# 헤더 색
for j in range(len(col_labels)):
    table[0, j].set_facecolor("#1E2761")
    table[0, j].set_text_props(color='white', fontweight='bold')

# TF-IDF 행 색
for i in range(1, 6):
    for j in range(len(col_labels)):
        table[i, j].set_facecolor("#EBF3FB")

# W2V 행 색
for i in range(6, 10):
    for j in range(len(col_labels)):
        table[i, j].set_facecolor("#FEF0EA")

# TF-IDF Total 강조
for j in range(len(col_labels)):
    table[5, j].set_facecolor("#C8E6C9")
    table[5, j].set_text_props(fontweight='bold')

ax.set_title("전체 모델 평가 결과 요약\n(*W2V 종합점수는 ILD 왜곡으로 인한 착시)",
             fontsize=13, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig("./chart_06_summary_table.png", dpi=150, bbox_inches='tight')
plt.close()
print("✅ chart_06_summary_table.png 저장")

print("\n🎉 총 6개 그래프 생성 완료!")
print("   chart_01_precision_mrr.png  — 막대: Precision & MRR 비교")
print("   chart_02_tfidf_trend.png    — 꺾은선: TF-IDF 단계별 변화")
print("   chart_03_radar.png          — 레이더: TF-IDF Total vs W2V 단계4")
print("   chart_04_heatmap.png        — 히트맵: 전 모델 × 전 지표")
print("   chart_05_scatter.png        — 산점도: Precision vs MRR")
print("   chart_06_summary_table.png  — 종합 요약표")