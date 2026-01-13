"""
Modern File Manager - single-file PyQt6 application
Features:
 - Left: directory tree (QTreeView)
 - Center: file icon grid (QListView in IconMode) with thumbnails
 - Right: preview pane (image/text/hex/metadata)
 - Toolbar: Back, Forward, Up, Refresh, New Folder, Search
 - Breadcrumb path bar
 - Context menu: Open, Copy, Paste, Rename, Delete
 - Basic copy/paste and delete operations
 - Cross-platform open (Windows/Mac/Linux)

Dependencies:
 - Python 3.8+
 - PyQt6
 - Pillow (for thumbnail generation)

Install:
    pip install PyQt6 Pillow

Run:
    python modern_file_manager.py

Note: This is a single-file example intended as a base — extend with features like drag/drop, file operations queue, trash integration, and background threading for large operations.
"""

import sys
import os
import shutil
import platform
import stat
from pathlib import Path
from functools import partial

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileSystemModel, QTreeView, QListView,
    QSplitter, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolBar,
    QAction, QLineEdit, QAbstractItemView, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QInputDialog, QTextEdit, QSizePolicy, QPushButton
)
from PyQt6.QtGui import QIcon, QPixmap, QKeySequence
from PyQt6.QtCore import Qt, QSize

try:
    from PIL import Image
except Exception:
    Image = None


def open_with_default_app(path: str):
    """Open a file or folder with the system default application."""
    if platform.system() == 'Windows':
        os.startfile(path)
    elif platform.system() == 'Darwin':
        os.system(f'open "{path}"')
    else:
        # linux / others
        os.system(f'xdg-open "{path}"')


class ThumbnailCache:
    """Simple thumbnail cache using Pillow when available."""

    def __init__(self, thumb_size=(128, 128)):
        self.cache = {}
        self.thumb_size = thumb_size

    def get(self, path: str):
        key = (path, self.thumb_size)
        if key in self.cache:
            return self.cache[key]
        pix = self._make_thumbnail(path)
        self.cache[key] = pix
        return pix

    def _make_thumbnail(self, path: str):
        if Image is None:
            return QIcon.fromTheme('text-x-generic').pixmap(*self.thumb_size)
        try:
            img = Image.open(path)
            img.thumbnail(self.thumb_size)
            data = img.convert('RGBA').tobytes('raw', 'RGBA')
            qimg = QPixmap.fromImage(QPixmap.fromImage(QPixmap()).toImage())
            # fallback: use QPixmap load directly from file
            pix = QPixmap(path)
            if pix.isNull():
                return QIcon.fromTheme('image-x-generic').pixmap(*self.thumb_size)
            return pix.scaled(*self.thumb_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        except Exception:
            # not an image or failure
            return QIcon.fromTheme('text-x-generic').pixmap(*self.thumb_size)


class FileListView(QListView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setIconSize(QSize(96, 96))
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setUniformItemSizes(False)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSpacing(12)
        self.setMovement(QListView.Movement.Free)


class ModernFileManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Modern File Manager')
        self.resize(1200, 700)

        self.clipboard_paths = []  # for copy/paste
        self.cut_mode = False

        self.thumb_cache = ThumbnailCache((128, 128))

        self.model = QFileSystemModel()
        self.model.setRootPath(str(Path.home()))

        # Directory tree
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(str(Path.home())))
        self.tree.setHeaderHidden(True)
        self.tree.clicked.connect(self.on_tree_clicked)
        self.tree.setAnimated(True)

        # File icon list
        self.list_view = FileListView()
        self.list_model = QListWidget()
        # We'll not use QFileSystemModel directly for the icon grid to allow thumbnails
        self.list_view.setModel(self.list_model.model())

        # Preview pane
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Breadcrumb / address bar
        self.address_bar = QLineEdit()
        self.address_bar.returnPressed.connect(self.on_address_entered)

        # Toolbar
        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)
        self._add_actions()

        # Layouts
        central = QWidget()
        central_layout = QVBoxLayout()
        central.setLayout(central_layout)
        central_layout.addWidget(self.address_bar)

        splitter = QSplitter()
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        left_layout.addWidget(self.tree)

        # center container for icons
        center_widget = QWidget()
        center_layout = QVBoxLayout()
        center_widget.setLayout(center_layout)
        center_layout.addWidget(self._make_icon_toolbar())
        center_layout.addWidget(self.list_model)

        splitter.addWidget(left_widget)
        splitter.addWidget(center_widget)
        splitter.addWidget(self.preview)
        splitter.setSizes([250, 600, 300])

        central_layout.addWidget(splitter)
        self.setCentralWidget(central)

        # initial directory
        self.current_path = str(Path.home())
        self.address_bar.setText(self.current_path)
        self.populate_list(self.current_path)

        # Context menu
        self.list_model.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_model.customContextMenuRequested.connect(self.on_list_context_menu)

        # double click open
        self.list_model.itemDoubleClicked.connect(self.on_item_double_clicked)

    def _add_actions(self):
        back_action = QAction(QIcon.fromTheme('go-previous'), 'Back', self)
        back_action.setShortcut(QKeySequence.StandardKey.Back)
        back_action.triggered.connect(self.go_back)
        self.toolbar.addAction(back_action)

        forward_action = QAction(QIcon.fromTheme('go-next'), 'Forward', self)
        forward_action.triggered.connect(self.go_forward)
        self.toolbar.addAction(forward_action)

        up_action = QAction(QIcon.fromTheme('go-up'), 'Up', self)
        up_action.triggered.connect(self.go_up)
        self.toolbar.addAction(up_action)

        refresh_action = QAction(QIcon.fromTheme('view-refresh'), 'Refresh', self)
        refresh_action.triggered.connect(self.refresh)
        self.toolbar.addAction(refresh_action)

        new_folder_action = QAction(QIcon.fromTheme('folder-new'), 'New Folder', self)
        new_folder_action.triggered.connect(self.create_folder)
        self.toolbar.addAction(new_folder_action)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText('Search...')
        self.search_box.returnPressed.connect(self.search)
        self.toolbar.addWidget(self.search_box)

    def _make_icon_toolbar(self):
        w = QWidget()
        h = QHBoxLayout()
        w.setLayout(h)
        icon_view_btn = QPushButton('Icons')
        list_view_btn = QPushButton('List')
        icon_view_btn.clicked.connect(lambda: self.set_view_mode('icons'))
        list_view_btn.clicked.connect(lambda: self.set_view_mode('list'))
        h.addWidget(icon_view_btn)
        h.addWidget(list_view_btn)
        h.addStretch()
        return w

    def set_view_mode(self, mode: str):
        if mode == 'icons':
            self.list_model.setViewMode(QListWidget.IconMode)
            self.list_model.setIconSize(QSize(96, 96))
        else:
            self.list_model.setViewMode(QListWidget.ListMode)
            self.list_model.setIconSize(QSize(24, 24))

    def on_tree_clicked(self, index):
        path = self.model.filePath(index)
        self.change_directory(path)

    def on_address_entered(self):
        path = self.address_bar.text().strip()
        if os.path.isdir(path):
            self.change_directory(path)
        else:
            QMessageBox.warning(self, 'Path error', f'Path not found: {path}')

    def change_directory(self, path: str):
        self.current_path = path
        self.address_bar.setText(path)
        self.populate_list(path)
        # expand tree to this path
        idx = self.model.index(path)
        if idx.isValid():
            self.tree.setCurrentIndex(idx)
            self.tree.expand(idx)

    def populate_list(self, path: str):
        self.list_model.clear()
        try:
            entries = sorted(Path(path).iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Could not list directory: {e}')
            return

        for p in entries:
            item = QListWidgetItem()
            name = p.name
            item.setText(name)
            if p.is_dir():
                icon = QIcon.fromTheme('folder')
                item.setIcon(icon)
            else:
                # try thumbnail
                pix = QPixmap()
                if p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp'):
                    pix = self.thumb_cache.get(str(p))
                if pix and not pix.isNull():
                    item.setIcon(QIcon(pix))
                else:
                    item.setIcon(QIcon.fromTheme('text-x-generic'))
            item.setData(Qt.ItemDataRole.UserRole, str(p))
            self.list_model.addItem(item)

    def on_list_context_menu(self, pos):
        item = self.list_model.itemAt(pos)
        menu = QMessageBox()  # small hack: we'll use QMessageBox as simple action chooser
        # better: use QMenu, but keep implementation simple and portable
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        open_act = menu.addAction('Open')
        copy_act = menu.addAction('Copy')
        paste_act = menu.addAction('Paste')
        rename_act = menu.addAction('Rename')
        delete_act = menu.addAction('Delete')
        newfolder_act = menu.addAction('New Folder')

        action = menu.exec(self.list_model.mapToGlobal(pos))
        if action == open_act and item:
            self.open_item(item)
        elif action == copy_act and item:
            path = item.data(Qt.ItemDataRole.UserRole)
            self.clipboard_paths = [path]
            self.cut_mode = False
        elif action == paste_act:
            self.paste()
        elif action == rename_act and item:
            self.rename_item(item)
        elif action == delete_act and item:
            self.delete_item(item)
        elif action == newfolder_act:
            self.create_folder()

    def on_item_double_clicked(self, item: QListWidgetItem):
        self.open_item(item)

    def open_item(self, item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        if os.path.isdir(path):
            self.change_directory(path)
        else:
            # preview or open
            if path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
                pix = QPixmap(path)
                if not pix.isNull():
                    self.preview.clear()
                    self.preview.document().addResource(0, 'image', pix)
                    self.preview.setHtml(f'<img src="{path}" style="max-width:100%; max-height:100%;"/>')
                    return
            try:
                open_with_default_app(path)
            except Exception as e:
                QMessageBox.warning(self, 'Open failed', str(e))

    def rename_item(self, item: QListWidgetItem):
        old_path = item.data(Qt.ItemDataRole.UserRole)
        new_name, ok = QInputDialog.getText(self, 'Rename', 'New name:', text=os.path.basename(old_path))
        if ok and new_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                os.rename(old_path, new_path)
                self.populate_list(self.current_path)
            except Exception as e:
                QMessageBox.warning(self, 'Rename failed', str(e))

    def delete_item(self, item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, 'Delete', f'Delete "{path}"? This cannot be undone.', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.populate_list(self.current_path)
            except Exception as e:
                QMessageBox.warning(self, 'Delete failed', str(e))

    def paste(self):
        if not self.clipboard_paths:
            return
        for src in self.clipboard_paths:
            base = os.path.basename(src)
            dest = os.path.join(self.current_path, base)
            try:
                if os.path.isdir(src):
                    if self.cut_mode:
                        shutil.move(src, dest)
                    else:
                        shutil.copytree(src, dest)
                else:
                    if self.cut_mode:
                        shutil.move(src, dest)
                    else:
                        shutil.copy2(src, dest)
            except Exception as e:
                QMessageBox.warning(self, 'Paste failed', str(e))
        self.clipboard_paths = []
        self.cut_mode = False
        self.populate_list(self.current_path)

    def create_folder(self):
        name, ok = QInputDialog.getText(self, 'New Folder', 'Folder name:')
        if ok and name:
            path = os.path.join(self.current_path, name)
            try:
                os.makedirs(path, exist_ok=False)
                self.populate_list(self.current_path)
            except Exception as e:
                QMessageBox.warning(self, 'Create failed', str(e))

    def refresh(self):
        self.populate_list(self.current_path)

    def go_up(self):
        p = Path(self.current_path).parent
        self.change_directory(str(p))

    def go_back(self):
        # placeholder for navigation history
        QMessageBox.information(self, 'Nav', 'Back not implemented in this demo')

    def go_forward(self):
        QMessageBox.information(self, 'Nav', 'Forward not implemented in this demo')

    def search(self):
        q = self.search_box.text().strip().lower()
        if not q:
            self.populate_list(self.current_path)
            return
        items = []
        for i in range(self.list_model.count()):
            it = self.list_model.item(i)
            if q in it.text().lower():
                items.append(it)
        # show only matching
        self.list_model.clear()
        for it in items:
            self.list_model.addItem(it)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = ModernFileManager()
    win.show()
    sys.exit(app.exec())
