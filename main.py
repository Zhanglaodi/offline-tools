from PySide6.QtWidgets import QApplication, QMainWindow, QToolBar
from PySide6.QtGui import QAction
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl
from PySide6.QtGui import QKeySequence
import sys, os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 WebView")

        # Web 视图
        self.view = QWebEngineView(self)
        self.setCentralWidget(self.view)

        # 主页（本地文件）
        self.home_path = os.path.abspath("./index.html")
        self.home_url = QUrl.fromLocalFile(self.home_path)
        self.view.load(self.home_url)

        # 工具栏
        tb = QToolBar("Nav", self)
        tb.setMovable(False)
        self.addToolBar(tb)

        # 后退
        self.act_back = QAction("← 后退", self)
        self.act_back.triggered.connect(self.view.back)
        self.act_back.setShortcut(QKeySequence("Alt+Left"))
        tb.addAction(self.act_back)

        # 前进
        self.act_fwd = QAction("前进 →", self)
        self.act_fwd.triggered.connect(self.view.forward)
        self.act_fwd.setShortcut(QKeySequence("Alt+Right"))
        tb.addAction(self.act_fwd)

        # 刷新
        self.act_reload = QAction("刷新", self)
        self.act_reload.triggered.connect(self.view.reload)
        # 常见快捷键：F5 或 Ctrl+R
        self.act_reload.setShortcuts([QKeySequence.Refresh, QKeySequence("Ctrl+R")])
        tb.addAction(self.act_reload)

        # 停止加载（可选）
        self.act_stop = QAction("停止", self)
        self.act_stop.triggered.connect(self.view.stop)
        tb.addAction(self.act_stop)

        # 主页
        self.act_home = QAction("主页", self)
        self.act_home.triggered.connect(self.load_home)
        self.act_home.setShortcut(QKeySequence("Alt+Home"))
        tb.addAction(self.act_home)

        # 根据历史记录可用性更新按钮状态
        self.view.loadFinished.connect(self.update_nav)
        self.view.urlChanged.connect(lambda _: self.update_nav())

        # 初始窗口大小
        self.resize(1200, 800)

    def load_home(self):
        self.view.load(self.home_url)

    def update_nav(self):
        h = self.view.history()
        # canGoBack / canGoForward 会在页面变化后更新
        self.act_back.setEnabled(h.canGoBack())
        self.act_fwd.setEnabled(h.canGoForward())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
