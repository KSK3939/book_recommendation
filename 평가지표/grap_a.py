import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import font_manager

# ==========================================
# 한글 폰트 설정
# ==========================================
font_path = '/home/user18/PycharmProjects/book_recommendation/malgun.ttf'

if os.path.exists(font_path):
    font_manager.fontManager.addfont(font_path)
    font_name = font_manager.FontProperties(fname=font_path).get_name()
    plt.rc('font', family=font_name)
else:
    plt.rc('font', family='NanumBarunGothic')

matplotlib.rcParams['axes.unicode_minus'] = False

# ==========================================
# 데이터
# ==========================================
stages = ["단계1\n(설명)", "단계2\n(+장르)", "단계3\n(+제목)", "단계4\n(+저자)", "Total\n(+국가)"]
tfidf_precision = [20.0, 19.8, 20.7, 23.7, 23.9]

# 색상
C_TFIDF = "#185FA5"
C_BG = "#F8F9FA"

# ==========================================
# TF-IDF Precision@10 변화 꺾은선 그래프
# ==========================================
fig, ax = plt.subplots(figsize=(8, 5), facecolor=C_BG)
ax.set_facecolor(C_BG)

x = np.arange(len(stages))

ax.plot(x, tfidf_precision, marker='o', linewidth=2.5, markersize=8, color=C_TFIDF)

# 값 표시
for i, v in enumerate(tfidf_precision):
    ax.annotate(f"{v:.1f}", (x[i], v),
                textcoords="offset points", xytext=(0, 8),
                ha='center', fontsize=10, fontweight='bold', color=C_TFIDF)

ax.set_xticks(x)
ax.set_xticklabels(stages, fontsize=10)
ax.set_ylabel("Precision@10 (%)", fontsize=11)
ax.set_title("TF-IDF Precision@10 변화", fontsize=14, fontweight='bold')
ax.grid(alpha=0.3)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig("./chart_tfidf_precision_line_country.png", dpi=150, bbox_inches='tight')
plt.show()