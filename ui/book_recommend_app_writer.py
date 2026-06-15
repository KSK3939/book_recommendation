import sys
import pandas as pd
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QCompleter
)
from PyQt5.QtCore import Qt, pyqtSignal

from book_recommender import BookRecommender

CSV_PATH = "../data/final_merge_preprocessed_writer.csv"
ORIG_CSV_PATH = "../data/final_merge.csv"

# 장르 체크박스 objectName -> 데이터의 장르 키워드 매핑
GENRE_CHECKBOX_MAP = {
    "chkMystery": "추리 미스터리",
    "chkSF": "SF",
    "chkRomance": "로맨스",
    "chkHorror": "공포 스릴러",
    "chkFantasy": "판타지",
    "chkHistory": "역사",
    "chkEtc": "기타",
}


class BookItem(QWidget):
    """검색 결과 리스트에 표시되는 개별 책 카드 (클릭 가능)"""

    clicked = pyqtSignal(int)  # csv row index 전달

    def __init__(self, book_index: int, book: dict, parent=None, alt: bool = False):
        super().__init__(parent)
        self.book_index = book_index
        self.setObjectName("bookItemAlt" if alt else "bookItem")
        self.setAttribute(Qt.WA_StyledBackground, True)
        bg_color = "#eef1f6" if alt else "#ffffff"
        self.setStyleSheet(
            f"QWidget#{'bookItemAlt' if alt else 'bookItem'} {{"
            f"background-color: {bg_color};"
            f"border: 1px solid #e4e8f0;"
            f"border-radius: 8px;"
            f"}}"
            f"QWidget#{'bookItemAlt' if alt else 'bookItem'}:hover {{"
            f"border: 1px solid #0080FF;"
            f"}}"
        )
        self.setFixedHeight(72)
        self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)

        # 정보 영역
        info = QVBoxLayout()
        info.setSpacing(3)
        info.setContentsMargins(0, 0, 0, 0)

        title = QLabel(str(book.get("제목", "")))
        title.setObjectName("bookTitleLabel")
        info.addWidget(title)

        author_text = f"{book.get('저자', '')} / {book.get('출판사', '')}"
        author = QLabel(author_text)
        author.setObjectName("bookAuthorLabel")
        info.addWidget(author)

        badge_row = QHBoxLayout()
        badge_row.setSpacing(6)
        badge_row.setContentsMargins(0, 0, 0, 0)

        genre_str = book.get("장르") or ""
        if genre_str:
            genre_badge = QLabel(genre_str)
            genre_badge.setObjectName("genreBadge")
            badge_row.addWidget(genre_badge)

        country_badge = QLabel(str(book.get("국가", "")))
        country_badge.setObjectName("countryBadge")
        badge_row.addWidget(country_badge)
        badge_row.addStretch()

        info.addLayout(badge_row)
        layout.addLayout(info)

    def mousePressEvent(self, event):
        self.clicked.emit(self.book_index)
        super().mousePressEvent(event)


class SimilarBooksPanel(QWidget):
    """클릭한 책 아래에 인라인으로 펼쳐지는 '책 설명 + 비슷한 책' 섹션"""

    def __init__(self, description: str, similar_books: list, parent=None):
        """
        Args:
            description: 클릭한 책의 원본 설명 텍스트
            similar_books: [(book_index, book_dict), ...]
        """
        super().__init__(parent)
        self.setObjectName("similarPanel")
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # 책 설명
        if description.strip():
            desc_title = QLabel("책 소개")
            desc_title.setObjectName("similarPanelTitle")
            layout.addWidget(desc_title)

            desc_label = QLabel(description.strip())
            desc_label.setObjectName("bookDescriptionLabel")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        # 유사 도서 추천
        title = QLabel("이 책과 비슷한 책")
        title.setObjectName("similarPanelTitle")
        layout.addWidget(title)

        for _, book in similar_books:
            row = QHBoxLayout()
            row.setSpacing(8)

            book_title = QLabel(str(book.get("제목", "")))
            book_title.setObjectName("similarBookTitle")
            row.addWidget(book_title)

            book_author = QLabel(str(book.get("저자", "")))
            book_author.setObjectName("similarBookAuthor")
            row.addWidget(book_author)

            row.addStretch()
            layout.addLayout(row)


class BookRecommendApp(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("book_recommend_app.ui", self)

        # 데이터 로드
        self.df = pd.read_csv(CSV_PATH)
        self.df["제목"] = self.df["제목"].fillna("")
        self.df["저자"] = self.df["저자"].fillna("")
        self.df["작가"] = self.df["작가"].fillna("")
        self.df["출판사"] = self.df["출판사"].fillna("")
        self.df["설명"] = self.df["설명"].fillna("")
        self.df["국가"] = self.df["국가"].fillna("")
        self.df["장르"] = self.df["장르"].fillna("").replace("", "기타")
        self.df.loc[self.df["장르"].str.strip() == "", "장르"] = "기타"

        # 원본(비전처리) 설명 로드 — ISBN 기준으로 매칭해 가독성 좋은 설명 사용
        df_orig = pd.read_csv(ORIG_CSV_PATH)
        df_orig = df_orig.drop_duplicates(subset="ISBN", keep="first")
        desc_map = dict(zip(df_orig["ISBN"], df_orig["설명"].fillna("")))
        self.df["설명_원본"] = self.df["ISBN"].map(desc_map).fillna("")

        # 추천 모델 로드 (TF-IDF + Word2Vec)
        self.recommender = BookRecommender()

        # 책 이름 자동완성
        titles = sorted(self.df["제목"].unique().tolist())
        title_completer = QCompleter(titles, self)
        title_completer.setCaseSensitivity(Qt.CaseInsensitive)
        title_completer.setFilterMode(Qt.MatchContains)
        self.bookNameInput.setCompleter(title_completer)

        # 저자/출판사 자동완성
        authors = self.df["작가"].unique().tolist()
        publishers = self.df["출판사"].unique().tolist()
        author_pub_values = sorted(set(authors + publishers) - {""})
        author_completer = QCompleter(author_pub_values, self)
        author_completer.setCaseSensitivity(Qt.CaseInsensitive)
        author_completer.setFilterMode(Qt.MatchContains)
        self.authorInput.setCompleter(author_completer)

        # 검색 버튼 연결
        self.searchBtn.clicked.connect(self.do_search)

        # 현재 펼쳐진 유사 도서 패널 추적 (한 번에 하나만 펼침)
        self.open_panel = None
        self.open_panel_book_index = None

        # 초기 빈 상태
        self.bookScrollArea.hide()

    def do_search(self):
        book_name = self.bookNameInput.text().strip()
        keyword = self.keywordInput.text().strip()
        author = self.authorInput.text().strip()
        country = self.countryCombo.currentText()
        if country == "전체":
            country = ""

        active_genres = [
            GENRE_CHECKBOX_MAP[name]
            for name, label in GENRE_CHECKBOX_MAP.items()
            if getattr(self, name).isChecked()
        ]

        results = self.df

        if book_name:
            # ISBN 검색: 입력값이 숫자이고 ISBN과 정확히 일치하면 해당 책만 반환
            if book_name.isdigit():
                isbn_match = results[results["ISBN"].astype(str) == book_name]
                if not isbn_match.empty:
                    self.display_results(isbn_match)
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
                results["작가"].str.contains(author, case=False, na=False)
                | results["저자"].str.contains(author, case=False, na=False)
                | results["출판사"].str.contains(author, case=False, na=False)
            )
            results = results[mask]

        if country:
            results = results[results["국가"] == country]

        if active_genres:
            mask = results["장르"].apply(
                lambda g: any(genre in g for genre in active_genres)
            )
            results = results[mask]

            # 선택한 장르를 더 많이 포함하는 책을 상위로 정렬
            # (모든 장르를 포함하는 책이 최상단에 오도록)
            match_count = results["장르"].apply(
                lambda g: sum(1 for genre in active_genres if genre in g)
            )
            results = results.assign(_genre_match=match_count)
            results = results.sort_values("_genre_match", ascending=False)
            results = results.drop(columns="_genre_match")

        # 키워드 기반 재정렬 (TF-IDF)
        if keyword and not results.empty:
            indices = results.index.tolist()
            ranked_indices = self.recommender.rank_by_keyword(keyword, indices)
            results = self.df.loc[ranked_indices]

        self.display_results(results)

    def display_results(self, results: pd.DataFrame):
        # 결과 개수 표시
        self.resultCount.setText(f"총 {len(results)}건")

        # 기존 결과 위젯 제거
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

        # 결과가 너무 많으면 상위 N개만 표시 (성능)
        max_display = 100
        for display_idx, (idx, row) in enumerate(results.head(max_display).iterrows()):
            item = BookItem(idx, row.to_dict(), alt=(display_idx % 2 == 1))
            item.clicked.connect(self.toggle_similar_panel)
            layout.addWidget(item)
            item.style().unpolish(item)
            item.style().polish(item)

        layout.addStretch()

    def toggle_similar_panel(self, book_index: int):
        """클릭한 책 아래에 '이 책과 비슷한 책' 패널을 토글합니다."""
        layout = self.bookListLayout

        # 이미 열려있는 패널이 있으면 제거
        if self.open_panel is not None:
            was_same = (self.open_panel_book_index == book_index)
            layout.removeWidget(self.open_panel)
            self.open_panel.deleteLater()
            self.open_panel = None
            self.open_panel_book_index = None
            if was_same:
                return  # 같은 책을 다시 클릭하면 닫기만 함

        # 클릭한 BookItem의 위치 찾기
        target_pos = None
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if isinstance(widget, BookItem) and widget.book_index == book_index:
                target_pos = i
                break

        if target_pos is None:
            return

        # 유사 도서 추천 (상위 5개)
        similar_indices = self.recommender.recommend_similar_books(book_index, top_n=5)
        similar_books = [(idx, self.df.iloc[idx].to_dict()) for idx in similar_indices]

        description = str(self.df.iloc[book_index].get("설명_원본", ""))

        panel = SimilarBooksPanel(description, similar_books)
        layout.insertWidget(target_pos + 1, panel)

        self.open_panel = panel
        self.open_panel_book_index = book_index


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = BookRecommendApp()
    w.show()
    sys.exit(app.exec_())