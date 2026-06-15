"""
playlist_recommend_app.py
장르/키워드 기반 플레이리스트 추천 팝업

외부에서 호출:
    from playlist_recommend_app import PlaylistRecommendApp
    dlg = PlaylistRecommendApp(book, parent=self)
    dlg.exec_()

단독 실행:
    python playlist_recommend_app.py
"""

import sys
import webbrowser
import pandas as pd
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QApplication, QDialog, QWidget,
    QHBoxLayout, QVBoxLayout, QLabel, QPushButton
)
from PyQt5.QtCore import Qt

# PLAYLIST_CSV = "../playlist_data/playlist_all.csv"
PLAYLIST_CSV = "../playlist_data/playlist_crawl.csv"


# playlist_all.csv genre 값 ↔ 책 장르 매핑
GENRE_MAP = {
    "추리 미스터리": "추리, 미스터리",
    "미스터리":      "추리, 미스터리",
    "추리":          "추리, 미스터리",
    "SF":            "SF",
    "로맨스":        "로맨스",
    "공포 스릴러":   "공포, 스릴러",
    "공포":          "공포, 스릴러",
    "스릴러":        "공포, 스릴러",
    "판타지":        "판타지",
    "역사":          "역사",
    "기타":          "기타",
}


def get_playlist_genres(book_genre: str) -> list:
    """책 장르 문자열에서 playlist CSV의 genre 값 목록 추출"""
    genres = set()
    for key, val in GENRE_MAP.items():
        if key in book_genre:
            genres.add(val)
    return list(genres) if genres else ["기타"]


def recommend_playlists(book: dict, top_n: int = 10) -> pd.DataFrame:
    """
    장르 우선 + 제목 키워드 보조로 플레이리스트 추천

    Args:
        book: 책 데이터 dict (제목, 장르 필수)
        top_n: 최대 추천 수

    Returns:
        pd.DataFrame (genre, title, duration, url)
    """
    try:
        df = pd.read_csv(PLAYLIST_CSV).fillna("")
    except FileNotFoundError:
        return pd.DataFrame(columns=["genre", "title", "duration", "url"])

    book_genre  = str(book.get("장르", "기타"))
    book_title  = str(book.get("제목", ""))
    keyword     = book_title.split()[0] if book_title.split() else ""

    target_genres = get_playlist_genres(book_genre)

    # 장르 일치 항목
    matched = df[df["genre"].isin(target_genres)].copy()
    others  = df[~df["genre"].isin(target_genres)].copy()

    # 키워드 보조 정렬
    if keyword and len(keyword) > 1:
        matched["_kw"] = matched["title"].str.contains(keyword, case=False, na=False).astype(int)
        matched = matched.sort_values("_kw", ascending=False).drop(columns="_kw")

    return pd.concat([matched, others], ignore_index=True).head(top_n)


class PlaylistItem(QWidget):
    """플레이리스트 개별 행 위젯"""

    def __init__(self, row: dict, alt: bool = False, parent=None):
        super().__init__(parent)
        obj = "plItemAlt" if alt else "plItem"
        self.setObjectName(obj)
        self.setAttribute(Qt.WA_StyledBackground, True)
        bg = "#eef1f6" if alt else "#ffffff"
        self.setStyleSheet(
            f"QWidget#{obj}{{background-color:{bg};border:1px solid #e4e8f0;border-radius:8px;}}"
        )
        self.setMinimumHeight(64)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        info = QVBoxLayout()
        info.setSpacing(3)
        info.setContentsMargins(0, 0, 0, 0)

        t = QLabel(str(row.get("title", "")))
        t.setObjectName("plItemTitle")
        t.setWordWrap(True)
        info.addWidget(t)

        meta = QHBoxLayout()
        meta.setSpacing(6)
        meta.setContentsMargins(0, 0, 0, 0)

        dur = QLabel(str(row.get("duration", "")))
        dur.setObjectName("plItemDuration")
        meta.addWidget(dur)

        genre = QLabel(str(row.get("genre", "")))
        genre.setObjectName("plItemGenre")
        meta.addWidget(genre)
        meta.addStretch()

        info.addLayout(meta)
        layout.addLayout(info)

        url = str(row.get("url", ""))
        btn = QPushButton("▶ 재생")
        btn.setObjectName("plPlayBtn")
        btn.setFixedSize(64, 28)
        btn.clicked.connect(lambda: webbrowser.open(url))
        layout.addWidget(btn)


class PlaylistRecommendApp(QDialog):
    """장르/키워드 기반 플레이리스트 추천 팝업"""

    def __init__(self, book: dict, parent=None):
        super().__init__(parent)
        uic.loadUi("playlist_recommend_app.ui", self)

        # 책 정보 주입
        self.plBookTitle.setText(str(book.get("제목", "")))
        self.plBookAuthor.setText(
            f"{book.get('저자', '')} / {book.get('출판사', '')}"
        )
        self.plGenreBadge.setText(str(book.get("장르", "")))

        # 플레이리스트 추천
        results = recommend_playlists(book, top_n=10)
        self.plCountLabel.setText(f"총 {len(results)}건")

        layout = self.plListLayout

        if results.empty:
            empty = QLabel("추천 플레이리스트가 없습니다.")
            empty.setObjectName("plEmptyLabel")
            empty.setAlignment(Qt.AlignCenter)
            layout.addWidget(empty)
        else:
            for i, (_, row) in enumerate(results.iterrows()):
                item = PlaylistItem(row.to_dict(), alt=(i % 2 == 1))
                layout.addWidget(item)
            layout.addStretch()

        self.plCloseBtn.clicked.connect(self.close)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    book = {"제목": "셜록 홈즈", "저자": "아서 코난 도일", "출판사": "시공사", "장르": "추리 미스터리"}
    dlg = PlaylistRecommendApp(book)
    dlg.show()
    sys.exit(app.exec_())