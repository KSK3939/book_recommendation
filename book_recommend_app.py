from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget
import sys

class BookRecommendApp(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("book_recommend_app.ui", self)
        self.searchBtn.clicked.connect(self.do_search)
        self.actionBtn.clicked.connect(self.do_search)

    def do_search(self):
        kw = self.searchInput.text()
        # 검색 로직 추가

app = QApplication(sys.argv)
w = BookRecommendApp()
w.show()
sys.exit(app.exec_())