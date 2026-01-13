import sys
import os
import shutil
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTreeView, QVBoxLayout,
                             QHBoxLayout, QWidget, QPushButton, QLineEdit,
                             QSplitter, QListView, QLabel,
                             QToolBar, QMenu, QMessageBox, QInputDialog, QFileDialog)
from PyQt6.QtCore import Qt, QDir, QFileInfo, QSize, QFileSystemModel
from PyQt6.QtGui import QAction


class ModernFileExplorer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modern File Explorer")
        self.setGeometry(100, 100, 1200, 700)

        # Apply modern dark theme
        self.apply_theme()

        # Initialize file system model
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())
        self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | QDir.AllDirs)

        # Store current path
        self.current_path = str(Path.home())

        # Setup UI
        self.setup_ui()

    def apply_theme(self):
        """Apply modern dark theme to the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
            }
            QTreeView, QListView {
                background-color: #282838;
                color: #e0e0e0;
                border: none;
                font-size: 13px;
                outline: none;
            }
            QTreeView::item:hover, QListView::item:hover {
                background-color: #3e3e4e;
            }
            QTreeView::item:selected, QListView::item:selected {
                background-color: #5e5ece;
            }
            QHeaderView::section {
                background-color: #1e1e2e;
                color: #e0e0e0;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QLineEdit {
                background-color: #282838;
                color: #e0e0e0;
                border: 2px solid #3e3e4e;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #5e5ece;
            }
            QPushButton {
                background-color: #5e5ece;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7e7eee;
            }
            QPushButton:pressed {
                background-color: #4e4ebe;
            }
            QToolBar {
                background-color: #1e1e2e;
                border: none;
                padding: 5px;
                spacing: 5px;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 12px;
            }
            QMenu {
                background-color: #282838;
                color: #e0e0e0;
                border: 1px solid #3e3e4e;
            }
            QMenu::item:selected {
                background-color: #5e5ece;
            }
        """)

    def setup_ui(self):
        """Setup the main user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Create toolbar
        self.create_toolbar()

        # Address bar
        address_layout = QHBoxLayout()
        self.address_bar = QLineEdit()
        self.address_bar.setText(self.current_path)
        self.address_bar.returnPressed.connect(self.navigate_to_path)
        address_layout.addWidget(QLabel("📂 Path:"))
        address_layout.addWidget(self.address_bar)

        go_button = QPushButton("Go")
        go_button.clicked.connect(self.navigate_to_path)
        address_layout.addWidget(go_button)

        main_layout.addLayout(address_layout)

        # Splitter for tree and list views
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Tree view (folder structure)
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(QDir.rootPath()))
        self.tree_view.setAnimated(True)
        self.tree_view.setIndentation(20)
        self.tree_view.setSortingEnabled(True)
        self.tree_view.setColumnWidth(0, 250)
        self.tree_view.clicked.connect(self.on_tree_clicked)
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)

        # List view (file details)
        self.list_view = QListView()
        self.list_view.setModel(self.model)
        self.list_view.setRootIndex(self.model.index(self.current_path))
        self.list_view.setViewMode(QListView.ViewMode.IconMode)
        self.list_view.setIconSize(QSize(64, 64))
        self.list_view.setGridSize(QSize(100, 100))
        self.list_view.setResizeMode(QListView.ResizeMode.Adjust)
        self.list_view.setWordWrap(True)
        self.list_view.doubleClicked.connect(self.on_item_double_clicked)
        self.list_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self.show_context_menu)

        splitter.addWidget(self.tree_view)
        splitter.addWidget(self.list_view)
        splitter.setSizes([300, 900])

        main_layout.addWidget(splitter)

        # Status bar
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)

    def create_toolbar(self):
        """Create toolbar with navigation and action buttons"""
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Back button
        back_action = QAction("⬅️ Back", self)
        back_action.triggered.connect(self.go_back)
        toolbar.addAction(back_action)

        # Forward button
        forward_action = QAction("➡️ Forward", self)
        forward_action.triggered.connect(self.go_forward)
        toolbar.addAction(forward_action)

        # Up button
        up_action = QAction("⬆️ Up", self)
        up_action.triggered.connect(self.go_up)
        toolbar.addAction(up_action)

        # Home button
        home_action = QAction("🏠 Home", self)
        home_action.triggered.connect(self.go_home)
        toolbar.addAction(home_action)

        toolbar.addSeparator()

        # Refresh button
        refresh_action = QAction("🔄 Refresh", self)
        refresh_action.triggered.connect(self.refresh_view)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        # New folder button
        new_folder_action = QAction("📁 New Folder", self)
        new_folder_action.triggered.connect(self.create_new_folder)
        toolbar.addAction(new_folder_action)

        # Delete button
        delete_action = QAction("🗑️ Delete", self)
        delete_action.triggered.connect(self.delete_item)
        toolbar.addAction(delete_action)

        toolbar.addSeparator()

        # View mode toggle
        icon_view_action = QAction("🖼️ Icons", self)
        icon_view_action.triggered.connect(lambda: self.set_view_mode(QListView.ViewMode.IconMode))
        toolbar.addAction(icon_view_action)

        list_view_action = QAction("📄 List", self)
        list_view_action.triggered.connect(lambda: self.set_view_mode(QListView.ViewMode.ListMode))
        toolbar.addAction(list_view_action)

    def on_tree_clicked(self, index):
        """Handle tree view item click"""
        path = self.model.filePath(index)
        if os.path.isdir(path):
            self.current_path = path
            self.address_bar.setText(path)
            self.list_view.setRootIndex(index)
            self.update_status()

    def on_item_double_clicked(self, index):
        """Handle double click on items"""
        path = self.model.filePath(index)
        if os.path.isdir(path):
            self.current_path = path
            self.address_bar.setText(path)
            self.list_view.setRootIndex(index)
            self.tree_view.setCurrentIndex(index)
            self.update_status()
        else:
            # Open file with default application
            try:
                if sys.platform == 'win32':
                    os.startfile(path)
                elif sys.platform == 'darwin':
                    os.system(f'open "{path}"')
                else:
                    os.system(f'xdg-open "{path}"')
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open file: {str(e)}")

    def navigate_to_path(self):
        """Navigate to path entered in address bar"""
        path = self.address_bar.text()
        if os.path.exists(path) and os.path.isdir(path):
            self.current_path = path
            index = self.model.index(path)
            self.list_view.setRootIndex(index)
            self.tree_view.setCurrentIndex(index)
            self.update_status()
        else:
            QMessageBox.warning(self, "Invalid Path", "The specified path does not exist or is not a directory.")
            self.address_bar.setText(self.current_path)

    def go_back(self):
        """Navigate back (placeholder for history implementation)"""
        self.update_status("Back navigation - implement history for full functionality")

    def go_forward(self):
        """Navigate forward (placeholder for history implementation)"""
        self.update_status("Forward navigation - implement history for full functionality")

    def go_up(self):
        """Navigate to parent directory"""
        parent = str(Path(self.current_path).parent)
        if parent != self.current_path:
            self.current_path = parent
            self.address_bar.setText(parent)
            index = self.model.index(parent)
            self.list_view.setRootIndex(index)
            self.tree_view.setCurrentIndex(index)
            self.update_status()

    def go_home(self):
        """Navigate to home directory"""
        self.current_path = str(Path.home())
        self.address_bar.setText(self.current_path)
        index = self.model.index(self.current_path)
        self.list_view.setRootIndex(index)
        self.tree_view.setCurrentIndex(index)
        self.update_status()

    def refresh_view(self):
        """Refresh the current view"""
        self.model.setRootPath("")
        self.model.setRootPath(QDir.rootPath())
        self.update_status("View refreshed")

    def create_new_folder(self):
        """Create a new folder in current directory"""
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and folder_name:
            new_path = os.path.join(self.current_path, folder_name)
            try:
                os.makedirs(new_path, exist_ok=True)
                self.refresh_view()
                self.update_status(f"Created folder: {folder_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create folder: {str(e)}")

    def delete_item(self):
        """Delete selected item"""
        index = self.list_view.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "No Selection", "Please select an item to delete.")
            return

        path = self.model.filePath(index)
        file_name = os.path.basename(path)

        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Are you sure you want to delete '{file_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.refresh_view()
                self.update_status(f"Deleted: {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete item: {str(e)}")

    def set_view_mode(self, mode):
        """Set the view mode for list view"""
        self.list_view.setViewMode(mode)
        if mode == QListView.ViewMode.IconMode:
            self.list_view.setIconSize(QSize(64, 64))
            self.list_view.setGridSize(QSize(100, 100))
        else:
            self.list_view.setIconSize(QSize(16, 16))
            self.list_view.setGridSize(QSize())

    def show_context_menu(self, position):
        """Show context menu for file operations"""
        menu = QMenu()

        open_action = menu.addAction("📂 Open")
        menu.addSeparator()
        copy_action = menu.addAction("📋 Copy")
        cut_action = menu.addAction("✂️ Cut")
        paste_action = menu.addAction("📄 Paste")
        menu.addSeparator()
        rename_action = menu.addAction("✏️ Rename")
        delete_action = menu.addAction("🗑️ Delete")
        menu.addSeparator()
        properties_action = menu.addAction("ℹ️ Properties")

        action = menu.exec(self.list_view.mapToGlobal(position))

        if action == delete_action:
            self.delete_item()
        elif action == properties_action:
            self.show_properties()

    def show_properties(self):
        """Show properties of selected item"""
        index = self.list_view.currentIndex()
        if not index.isValid():
            return

        path = self.model.filePath(index)
        file_info = QFileInfo(path)

        info_text = f"""
        Name: {file_info.fileName()}
        Path: {file_info.filePath()}
        Size: {self.format_size(file_info.size())}
        Type: {'Directory' if file_info.isDir() else 'File'}
        Modified: {file_info.lastModified().toString()}
        """

        QMessageBox.information(self, "Properties", info_text)

    def format_size(self, size):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    def update_status(self, message=None):
        """Update status bar"""
        if message:
            self.status_label.setText(message)
        else:
            try:
                items = os.listdir(self.current_path)
                dirs = sum(1 for item in items if os.path.isdir(os.path.join(self.current_path, item)))
                files = len(items) - dirs
                self.status_label.setText(f"📁 {dirs} folders | 📄 {files} files | Current: {self.current_path}")
            except:
                self.status_label.setText(f"Current: {self.current_path}")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    explorer = ModernFileExplorer()
    explorer.show()

    sys.exit(app.exec())


if __name__ == "__main__":

    main()

