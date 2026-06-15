"""
recommend_system.py
book_recommend_app 기반 AI 추천 시스템

book_recommend_app.py 와 동일한 검색 기능에 추가로:
- 책 카드 클릭 시 토글 패널에 "추천 플레이리스트" 버튼 추가
- 버튼 클릭 시 playlist_recommend_app (PlaylistRecommendApp) 팝업 실행
"""

import sys
import pandas as pd
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QCompleter, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal

from book_recommender import BookRecommender
from playlist_recommend_app import PlaylistRecommendApp

CSV_PATH      = "../data/final_merge_preprocessed_writer.csv"
ORIG_CSV_PATH = "../data/final_merge.csv"

GENRE_CHECKBOX_MAP = {
    "chkMystery": "추리 미스터리",
    "chkSF":      "SF",
    "chkRomance": "로맨스",
    "chkHorror":  "공포 스릴러",
    "chkFantasy": "판타지",
    "chkHistory": "역사",
    "chkEtc":     "기타",
}


# ── 책 카드 ───────────────────────────────────
class BookItem(QWidget):
    clicked = pyqtSignal(int)

    def __init__(self, book_index: int, book: dict, alt: bool = False, parent=None):
        super().__init__(parent)
        self.book_index = book_index
        obj = "bookItemAlt" if alt else "bookItem"
        self.setObjectName(obj)
        self.setAttribute(Qt.WA_StyledBackground, True)
        bg = "#eef1f6" if alt else "#ffffff"
        self.setStyleSheet(
            f"QWidget#{obj}{{background-color:{bg};border:1px solid #e4e8f0;border-radius:8px;}}"
            f"QWidget#{obj}:hover{{border:1px solid #0080FF;}}"
        )
        self.setFixedHeight(72)
        self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)

        info = QVBoxLayout()
        info.setSpacing(3)
        info.setContentsMargins(0, 0, 0, 0)

        t = QLabel(str(book.get("제목", "")))
        t.setObjectName("bookTitleLabel")
        info.addWidget(t)

        작가 = str(book.get("작가", "")).strip()
        출판사 = str(book.get("출판사", "")).strip()
        author_text = f"{작가} / {출판사}" if 작가 else f"{출판사}"
        a = QLabel(author_text)
        a.setObjectName("bookAuthorLabel")
        info.addWidget(a)

        br = QHBoxLayout()
        br.setSpacing(6)
        br.setContentsMargins(0, 0, 0, 0)

        genre_str = book.get("장르") or ""
        if genre_str:
            g = QLabel(genre_str)
            g.setObjectName("genreBadge")
            br.addWidget(g)

        c = QLabel(str(book.get("국가", "")))
        c.setObjectName("countryBadge")
        br.addWidget(c)
        br.addStretch()
        info.addLayout(br)
        layout.addLayout(info)

    def mousePressEvent(self, event):
        self.clicked.emit(self.book_index)
        super().mousePressEvent(event)


# ── 토글 패널: 소개 + 유사도서 + 플레이리스트 버튼 ──
class BookDetailPanel(QWidget):
    playlist_requested = pyqtSignal(dict)

    def __init__(self, description: str, similar_books: list, book: dict, parent=None):
        super().__init__(parent)
        self.book = book
        self.setObjectName("similarPanel")
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # 책 소개
        if description.strip():
            t = QLabel("책 소개")
            t.setObjectName("similarPanelTitle")
            layout.addWidget(t)

            d = QLabel(description.strip())
            d.setObjectName("bookDescriptionLabel")
            d.setWordWrap(True)
            layout.addWidget(d)

        # 유사 도서
        t2 = QLabel("이 책과 비슷한 책")
        t2.setObjectName("similarPanelTitle")
        layout.addWidget(t2)

        for _, b in similar_books:
            row = QHBoxLayout()
            row.setSpacing(8)
            tl = QLabel(str(b.get("제목", "")))
            tl.setObjectName("similarBookTitle")
            row.addWidget(tl)
            작가 = str(b.get("작가", "")).strip()
            출판사 = str(b.get("출판사", "")).strip()
            al = QLabel(f"{작가} / {출판사}" if 작가 else 출판사)
            al.setObjectName("similarBookAuthor")
            row.addWidget(al)
            row.addStretch()
            layout.addLayout(row)

        # 플레이리스트 버튼
        btn = QPushButton("♪  추천 플레이리스트")
        btn.setObjectName("playlistBtn")
        btn.clicked.connect(lambda: self.playlist_requested.emit(self.book))
        layout.addWidget(btn)


# ── 메인 앱 ──────────────────────────────────
class RecommendSystemApp(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("recommend_system.ui", self)

        # 데이터 로드
        self.df = pd.read_csv(CSV_PATH)
        for col in ["제목", "저자", "작가", "출판사", "설명", "국가"]:
            self.df[col] = self.df[col].fillna("")
        self.df["장르"] = self.df["장르"].fillna("")
        self.df.loc[self.df["장르"].str.strip() == "", "장르"] = "기타"

        df_orig = pd.read_csv(ORIG_CSV_PATH).drop_duplicates(subset="ISBN", keep="first")
        desc_map = dict(zip(df_orig["ISBN"], df_orig["설명"].fillna("")))
        self.df["설명_원본"] = self.df["ISBN"].map(desc_map).fillna("")

        self.recommender = BookRecommender()

        # 자동완성 — 책 이름
        tc = QCompleter(sorted(self.df["제목"].unique().tolist()), self)
        tc.setCaseSensitivity(Qt.CaseInsensitive)
        tc.setFilterMode(Qt.MatchContains)
        self.bookNameInput.setCompleter(tc)

        # 자동완성 — 저자/작가/출판사
        ap = sorted(set(self.df["작가"].tolist()) - {""})
        ac = QCompleter(ap, self)
        ac.setCaseSensitivity(Qt.CaseInsensitive)
        ac.setFilterMode(Qt.MatchContains)
        self.authorInput.setCompleter(ac)

        self.searchBtn.clicked.connect(self.do_search)

        self.open_panel = None
        self.open_panel_book_index = None
        self.bookScrollArea.hide()

    def do_search(self):
        book_name = self.bookNameInput.text().strip()
        keyword   = self.keywordInput.text().strip()
        author    = self.authorInput.text().strip()
        country   = self.countryCombo.currentText()
        if country == "전체":
            country = ""

        active_genres = [
            GENRE_CHECKBOX_MAP[n]
            for n in GENRE_CHECKBOX_MAP
            if getattr(self, n).isChecked()
        ]

        results = self.df

        if book_name:
            if book_name.isdigit():
                m = results[results["ISBN"].astype(str) == book_name]
                if not m.empty:
                    self.display_results(m)
                    return
            results = results[results["제목"].str.contains(book_name, case=False, na=False)]

        if keyword:
            mask = (
                results["제목"].str.contains(keyword, case=False, na=False)
                | results["설명"].str.contains(keyword, case=False, na=False)
            )
            results = results[mask]

        if author:
            mask = (
                results["저자"].str.contains(author, case=False, na=False)
                | results["작가"].str.contains(author, case=False, na=False)
                | results["출판사"].str.contains(author, case=False, na=False)
            )
            results = results[mask]

        if country:
            results = results[results["국가"] == country]

        if active_genres:
            mask = results["장르"].apply(lambda g: any(genre in g for genre in active_genres))
            results = results[mask]
            mc = results["장르"].apply(lambda g: sum(1 for genre in active_genres if genre in g))
            results = results.assign(_gm=mc).sort_values("_gm", ascending=False).drop(columns="_gm")

        if keyword and not results.empty:
            ranked = self.recommender.rank_by_keyword(keyword, results.index.tolist())
            results = self.df.loc[ranked]

        self.display_results(results)

    def display_results(self, results: pd.DataFrame):
        self.resultCount.setText(f"총 {len(results)}건")

        layout = self.bookListLayout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.open_panel = None
        self.open_panel_book_index = None

        if results.empty:
            self.emptyLabel.setText("검색 결과가 없습니다.")
            self.emptyLabel.show()
            self.bookScrollArea.hide()
            return

        self.emptyLabel.hide()
        self.bookScrollArea.show()

        for disp_idx, (idx, row) in enumerate(results.head(100).iterrows()):
            item = BookItem(idx, row.to_dict(), alt=(disp_idx % 2 == 1))
            item.clicked.connect(self.toggle_detail_panel)
            layout.addWidget(item)
            item.style().unpolish(item)
            item.style().polish(item)

        layout.addStretch()

    def toggle_detail_panel(self, book_index: int):
        layout = self.bookListLayout

        if self.open_panel is not None:
            was_same = (self.open_panel_book_index == book_index)
            layout.removeWidget(self.open_panel)
            self.open_panel.deleteLater()
            self.open_panel = None
            self.open_panel_book_index = None
            if was_same:
                return

        target_pos = None
        for i in range(layout.count()):
            w = layout.itemAt(i).widget()
            if isinstance(w, BookItem) and w.book_index == book_index:
                target_pos = i
                break

        if target_pos is None:
            return

        similar_indices = self.recommender.recommend_similar_books(book_index, top_n=5)
        similar_books   = [(i, self.df.iloc[i].to_dict()) for i in similar_indices]
        book_data       = self.df.iloc[book_index].to_dict()
        description     = str(self.df.iloc[book_index].get("설명_원본", ""))

        panel = BookDetailPanel(description, similar_books, book_data)
        panel.playlist_requested.connect(self.open_playlist)
        layout.insertWidget(target_pos + 1, panel)

        self.open_panel = panel
        self.open_panel_book_index = book_index

    def open_playlist(self, book: dict):
        dlg = PlaylistRecommendApp(book, self)
        dlg.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = RecommendSystemApp()
    w.show()
    sys.exit(app.exec_())