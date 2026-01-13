# file_manager.py
import sys, os, shutil
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTreeView, QListView, QSplitter,
    QVBoxLayout, QToolBar, QAction, QLineEdit, QFileDialog, QMessageBox,
    QHBoxLayout, QLabel, QFrame, QMenu
)
from PySide6.QtGui import QIcon, QKeySequence
from PySide6.QtCore import Qt, QDir, QSize, QModelIndex
from PySide6.QtWidgets import QFileSystemModel, QTextEdit
from PIL import Image

class FileManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modern File Manager")
        self.resize(1100, 700)
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())

        # Toolbar
        tb = QToolBar()
        tb.setIconSize(QSize(20,20))
        self.addToolBar(tb)
        self.back_act = QAction(QIcon.fromTheme("go-previous"), "Back", self)
        self.up_act = QAction(QIcon.fromTheme("go-up"), "Up", self)
        self.refresh_act = QAction(QIcon.fromTheme("view-refresh"), "Refresh", self)
        self.new_folder_act = QAction(QIcon.fromTheme("folder-new"), "New Folder", self)
        tb.addAction(self.back_act); tb.addAction(self.up_act); tb.addAction(self.refresh_act); tb.addAction(self.new_folder_act)
        tb.addSeparator()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search current folder...")
        self.search.setMaximumWidth(300)
        tb.addWidget(self.search)

        # Splitter: left tree, right vertical (icons + preview)
        splitter = QSplitter()
        left = QTreeView()
        left.setModel(self.model)
        left.setRootIndex(self.model.index(QDir.homePath()))
        left.setHeaderHidden(True)
        left.setAnimated(True)
        left.setIndentation(12)
        left.setColumnHidden(1, True); left.setColumnHidden(2, True); left.setColumnHidden(3, True)

        right_split = QSplitter(Qt.Vertical)
        self.icon_view = QListView()
        self.icon_view.setViewMode(QListView.IconMode)
        self.icon_view.setIconSize(QSize(64,64))
        self.icon_view.setModel(self.model)
        self.icon_view.setRootIndex(self.model.index(QDir.homePath()))
        self.icon_view.setSpacing(12)
        self.icon_view.setResizeMode(QListView.Adjust)

        # Preview pane
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setMinimumHeight(150)

        right_split.addWidget(self.icon_view)
        right_split.addWidget(self.preview)
        splitter.addWidget(left)
        splitter.addWidget(right_split)
        splitter.setStretchFactor(1, 2)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(splitter)
        self.setCentralWidget(container)

        # Connections
        left.selectionModel().selectionChanged.connect(self.on_tree_selection)
        self.icon_view.clicked.connect(self.on_icon_clicked)
        self.search.returnPressed.connect(self.on_search)
        self.refresh_act.triggered.connect(self.on_refresh)
        self.up_act.triggered.connect(self.on_up)
        self.new_folder_act.triggered.connect(self.on_new_folder)

        # Context menu
        self.icon_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.icon_view.customContextMenuRequested.connect(self.on_context_menu)

    def on_tree_selection(self, selected, _):
        idx = selected.indexes()[0]
        path = self.model.filePath(idx)
        self.icon_view.setRootIndex(self.model.index(path))

    def on_icon_clicked(self, index: QModelIndex):
        path = self.model.filePath(index)
        if os.path.isdir(path):
            self.icon_view.setRootIndex(self.model.index(path))
        else:
            self.preview_file(path)

    def preview_file(self, path):
        try:
            if path.lower().endswith(('.png','.jpg','.jpeg','.bmp','.gif')):
                self.preview.setHtml(f"<img src='file://{path}' width='100%'>")
            else:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read(10000)
                self.preview.setPlainText(text)
        except Exception as e:
            self.preview.setPlainText(f"Cannot preview: {e}")

    def on_search(self):
        term = self.search.text().lower()
        root = self.icon_view.rootIndex()
        root_path = self.model.filePath(root)
        matches = []
        for name in os.listdir(root_path):
            if term in name.lower():
                matches.append(name)
        # simple: show first match by setting root to parent and selecting
        if matches:
            QMessageBox.information(self, "Search", f"Found: {', '.join(matches[:10])}")
        else:
            QMessageBox.information(self, "Search", "No matches")

    def on_refresh(self):
        self.model.refresh()

    def on_up(self):
        current = self.icon_view.rootIndex()
        path = self.model.filePath(current)
        parent = os.path.dirname(path)
        if parent:
            self.icon_view.setRootIndex(self.model.index(parent))

    def on_new_folder(self):
        root = self.icon_view.rootIndex()
        path = self.model.filePath(root)
        name, ok = QFileDialog.getSaveFileName(self, "New Folder Name", os.path.join(path, "New Folder"))
        if ok and name:
            try:
                os.makedirs(name, exist_ok=True)
                self.model.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def on_context_menu(self, pos):
        idx = self.icon_view.indexAt(pos)
        if not idx.isValid(): return
        path = self.model.filePath(idx)
        menu = QMenu()
        open_act = menu.addAction("Open")
        rename_act = menu.addAction("Rename")
        delete_act = menu.addAction("Delete")
        act = menu.exec(self.icon_view.mapToGlobal(pos))
        if act == open_act:
            if os.path.isdir(path):
                self.icon_view.setRootIndex(self.model.index(path))
            else:
                os.startfile(path) if sys.platform.startswith('win') else os.system(f'xdg-open "{path}"')
        elif act == delete_act:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.model.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Delete failed", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    fm = FileManager()
    fm.show()
    sys.exit(app.exec())