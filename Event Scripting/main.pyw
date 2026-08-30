"""
FE3H Event Script Editor - Main Window
"""

import json
import os
import ctypes
import sys
import struct

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QFileDialog,
    QMessageBox, QToolBar, QStatusBar, QFontDialog, QLabel,
    QWidget, QVBoxLayout, QInputDialog, QPlainTextEdit,
    QStackedWidget, QToolButton, QButtonGroup
)
from PySide6.QtGui import QAction, QActionGroup, QFont, QKeySequence, QTextCursor, QTextFormat, QIcon

from model import ScriptModel, ScriptEntry
from text_view import ScriptTextView
from property_panel import PropertyPanel
from control_flow import analyze_control_flow
from find_replace import FindReplaceBar
from block_view import BlockView

#
# Environment variables (for PyInstaller)
#

# Set the app user model ID before creating QApplication (Windows only)
if sys.platform == "win32":
    myappid = "com.niltwill.fetheveditor.1.0"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

# Determine the base directory for resource files
if getattr(sys, "frozen", False):
    basedir = sys._MEIPASS
else:
    basedir = os.path.dirname(__file__)

# The path for resource dir
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

#
# Settings
#
SETTINGS_FILE = resource_path("editor-settings.json")
DEFAULT_SETTINGS = {
    "last_directory": "",
    "mode_view": 0,
    "show_block_connectors": True,
    "show_warnings": True,
    "word_wrap": False,
    "font_family": "Consolas",
    "font_size": 10,
    "zoom_delta": 0,
    "window_width": 1280,
    "window_height": 800,
    "window_maximized": False,
}


def load_settings() -> dict:
    try:
        with open(SETTINGS_FILE, "r") as f:
            saved = json.load(f)
        merged = dict(DEFAULT_SETTINGS)
        merged.update(saved)
        return merged
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FE3H Event Script Editor")
        #self.setWindowIcon(QIcon('fe3h-se-icon.png'))
        self.setWindowIcon(QIcon((os.path.join(basedir, "fe3h-se-icon.ico"))))

        self._display_path: str | None = None
        self._settings = load_settings()
        self.resize(self._settings["window_width"], self._settings["window_height"])

        # Model
        self.model = ScriptModel(self)
        self._syncing = False
        self._text_dirty = False

        # Central: Stacked View (Text + Block)
        self._view_stack = QStackedWidget()

        # Page 0: Block view (default)
        self.block_view = BlockView(self.model, self)
        self.block_view.entry_clicked.connect(self._on_block_clicked)
        self.block_view.param_changed.connect(self._on_block_param_changed)
        self.block_view.entry_moved.connect(self._on_block_entry_moved)
        self._view_stack.addWidget(self.block_view)

        # Page 1: Text view + find bar
        text_page = QWidget()
        text_layout = QVBoxLayout(text_page)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)

        self.text_view = ScriptTextView()
        self.text_view.line_clicked.connect(self._on_line_clicked)
        self.text_view.textChanged.connect(self._on_text_changed)

        self.find_bar = FindReplaceBar(self.text_view)
        self.find_bar.status_message.connect(self._on_find_status)
        text_layout.addWidget(self.find_bar)
        text_layout.addWidget(self.text_view, stretch=1)

        self._view_stack.addWidget(text_page)

        self.setCentralWidget(self._view_stack)

        # Apply mode view (0 = block, 1 = text)
        self._current_view = self._settings.get("mode_view", 0)
        self._view_stack.setCurrentIndex(self._current_view)

        # Apply saved font + zoom
        font = QFont(self._settings["font_family"], self._settings["font_size"])
        self.text_view.setFont(font)
        if self._settings["zoom_delta"] != 0:
            self.text_view.zoomIn(self._settings["zoom_delta"])

        # Apply saved block view zoom
        block_zoom = self._settings.get("block_zoom_delta", 0)
        if block_zoom != 0:
            scale = 1.1 ** block_zoom
            self.block_view.scale(scale, scale)

        # Apply saved warnings state
        self.text_view.show_warnings = self._settings["show_warnings"]

        # Apply saved block connector state
        self.block_view._scene.show_connectors = self._settings.get("show_block_connectors", True)

        # Apply saved word wrapping state
        self.text_view.word_wrap = self._settings["word_wrap"]

        # Right Dock: Property Panel
        self.prop_panel = PropertyPanel(self.model)
        self.prop_panel.param_changed.connect(self._on_param_changed)

        self._prop_dock = QDockWidget("Properties", self)
        self._prop_dock.setWidget(self.prop_panel)
        self._prop_dock.setMinimumWidth(300)
        self._prop_dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable
        )
        self.addDockWidget(Qt.RightDockWidgetArea, self._prop_dock)

        # Connect model signals
        self.model.entries_changed.connect(self._sync_model_to_text)
        self.model.entry_modified.connect(self._on_entry_modified)
        self.model.entry_inserted.connect(self._sync_model_to_text)
        self.model.entry_removed.connect(self._sync_model_to_text)
        self.model.entries_moved.connect(self._sync_model_to_text)
        self.model.dirty_changed.connect(self._update_title)

        # Undo/redo availability from both sources
        self.model.undo_stack.canUndoChanged.connect(self._update_undo_state)
        self.model.undo_stack.canRedoChanged.connect(self._update_undo_state)
        self.text_view.undoAvailable.connect(self._update_undo_state)
        self.text_view.redoAvailable.connect(self._update_undo_state)

        # Menus + Toolbar
        self._create_menus()
        self._create_toolbar()

        # Status Bar
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status_label = QLabel("Ready")
        self._status.addWidget(self._status_label)
        self._type_count_label = QLabel("")
        self._status.addPermanentWidget(self._type_count_label)
        self._zoom_label = QLabel("100%")
        self._status.addPermanentWidget(self._zoom_label)
        self._entry_count_label = QLabel("")
        self._status.addPermanentWidget(self._entry_count_label)

        # Apply initial statusbar visibility
        if not self._settings.get("show_statusbar", True):
            self._status.hide()

        # Apply initial word wrap
        if self._settings.get("word_wrap", False):
            self.text_view.setLineWrapMode(QPlainTextEdit.WidgetWidth)

        # Theme (scoped to avoid bleeding into dialogs)
        self._apply_dark_theme()
        self._update_title()

        # Block view is default - hide text-only menu items initially
        for act in self._text_only_actions:
            act.setVisible(False)
        for act in self._text_only_view_actions:
            act.setVisible(False)
        for act in self._block_only_actions:
            act.setVisible(self._current_view == 0)

    def _create_menus(self):
        mb = self.menuBar()

        # File
        file_menu = mb.addMenu("&File")

        open_bin = QAction("Open &Binary (.bin)...", self)
        open_bin.setShortcut(QKeySequence("Ctrl+O"))
        open_bin.triggered.connect(self._open_bin)
        file_menu.addAction(open_bin)

        open_txt = QAction("Open &Text (.txt)...", self)
        open_txt.setShortcut(QKeySequence("Ctrl+Shift+O"))
        open_txt.triggered.connect(self._open_txt)
        file_menu.addAction(open_txt)

        file_menu.addSeparator()

        close_act = QAction("&Close", self)
        close_act.setShortcut(QKeySequence("Ctrl+W"))
        close_act.triggered.connect(self._close_file)
        file_menu.addAction(close_act)

        file_menu.addSeparator()

        save_txt = QAction("&Save Text", self)
        save_txt.setShortcut(QKeySequence("Ctrl+S"))
        save_txt.triggered.connect(self._save_txt)
        file_menu.addAction(save_txt)

        save_txt_as = QAction("Save Text &As...", self)
        save_txt_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_txt_as.triggered.connect(self._save_txt_as)
        file_menu.addAction(save_txt_as)

        file_menu.addSeparator()

        build_bin = QAction("&Build Binary (.bin)...", self)
        build_bin.setShortcut(QKeySequence("Ctrl+B"))
        build_bin.triggered.connect(self._build_bin)
        file_menu.addAction(build_bin)

        file_menu.addSeparator()

        quit_act = QAction("&Quit", self)
        quit_act.setShortcut(QKeySequence("Ctrl+Q"))
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

        # Edit
        edit_menu = mb.addMenu("&Edit")

        # Track actions that should be hidden in block mode
        self._text_only_actions = []
        self._block_only_actions = []

        self._undo_action = QAction("&Undo", self)
        self._undo_action.setShortcut(QKeySequence.Undo)
        self._undo_action.setEnabled(False)
        self._undo_action.triggered.connect(self._do_undo)
        edit_menu.addAction(self._undo_action)

        self._redo_action = QAction("&Redo", self)
        self._redo_action.setShortcut(QKeySequence.Redo)
        self._redo_action.setEnabled(False)
        self._redo_action.triggered.connect(self._do_redo)
        edit_menu.addAction(self._redo_action)

        edit_menu.addSeparator()

        cut_act = QAction("Cu&t", self)
        cut_act.setShortcut(QKeySequence.Cut)
        cut_act.triggered.connect(self.text_view.cut)
        edit_menu.addAction(cut_act)

        copy_act = QAction("&Copy", self)
        copy_act.setShortcut(QKeySequence.Copy)
        copy_act.triggered.connect(self.text_view.copy)
        edit_menu.addAction(copy_act)

        paste_act = QAction("&Paste", self)
        paste_act.setShortcut(QKeySequence.Paste)
        paste_act.triggered.connect(self.text_view.paste)
        edit_menu.addAction(paste_act)

        del_act = QAction("De&lete", self)
        del_act.setShortcut(QKeySequence.Delete)
        del_act.triggered.connect(self._delete_selection)
        edit_menu.addAction(del_act)

        # These clipboard actions only work in text mode
        self._text_only_actions.extend([cut_act, copy_act, paste_act, del_act])

        edit_menu.addSeparator()

        insert_before = QAction("Insert Entry &Before", self)
        insert_before.setShortcut(QKeySequence("Ctrl+Shift+Return"))
        insert_before.triggered.connect(self._insert_before)
        edit_menu.addAction(insert_before)

        insert_after = QAction("Insert Entry &After", self)
        insert_after.setShortcut(QKeySequence("Ctrl+Return"))
        insert_after.triggered.connect(self._insert_after)
        edit_menu.addAction(insert_after)

        delete_entry = QAction("Delete Entr&y", self)
        delete_entry.setShortcut(QKeySequence("Ctrl+Shift+K"))
        delete_entry.triggered.connect(self._delete_entry)
        edit_menu.addAction(delete_entry)

        edit_menu.addSeparator()

        duplicate = QAction("Du&plicate Entry", self)
        duplicate.setShortcut(QKeySequence("Ctrl+D"))
        duplicate.triggered.connect(self._duplicate_entry)
        edit_menu.addAction(duplicate)

        move_up = QAction("Move Entry &Up", self)
        move_up.setShortcut(QKeySequence("Alt+Up"))
        move_up.triggered.connect(self._move_up)
        edit_menu.addAction(move_up)

        move_down = QAction("Move Entry Do&wn", self)
        move_down.setShortcut(QKeySequence("Alt+Down"))
        move_down.triggered.connect(self._move_down)
        edit_menu.addAction(move_down)

        edit_menu.addSeparator()

        reindex = QAction("Re&index All Entries", self)
        reindex.setShortcut(QKeySequence("Ctrl+I"))
        reindex.triggered.connect(self._reindex)
        edit_menu.addAction(reindex)

        edit_menu.addSeparator()

        find_act = QAction("&Find...", self)
        find_act.setShortcut(QKeySequence("Ctrl+F"))
        find_act.triggered.connect(self._open_find)
        edit_menu.addAction(find_act)
        self._text_only_actions.append(find_act)

        find_replace_act = QAction("Find && &Replace...", self)
        find_replace_act.setShortcut(QKeySequence("Ctrl+H"))
        find_replace_act.triggered.connect(self._open_find_replace)
        edit_menu.addAction(find_replace_act)
        self._text_only_actions.append(find_replace_act)

        go_to_act = QAction("&Go to Entry...", self)
        go_to_act.setShortcut(QKeySequence("Ctrl+G"))
        go_to_act.triggered.connect(self._go_to_entry)
        edit_menu.addAction(go_to_act)

        edit_menu.addSeparator()

        self._nav_next_type = QAction("Next Same Event Type", self)
        self._nav_next_type.setShortcut(QKeySequence("Alt+Right"))
        self._nav_next_type.triggered.connect(lambda: self._navigate_same_type(1))
        edit_menu.addAction(self._nav_next_type)

        self._nav_prev_type = QAction("Previous Same Event Type", self)
        self._nav_prev_type.setShortcut(QKeySequence("Alt+Left"))
        self._nav_prev_type.triggered.connect(lambda: self._navigate_same_type(-1))
        edit_menu.addAction(self._nav_prev_type)

        edit_menu.addSeparator()

        select_all_act = QAction("Select &All", self)
        select_all_act.setShortcut(QKeySequence.SelectAll)
        select_all_act.triggered.connect(self.text_view.selectAll)
        edit_menu.addAction(select_all_act)
        self._text_only_actions.append(select_all_act)

        select_type_act = QAction("&Select All Current Event Type", self)
        select_type_act.setShortcut(QKeySequence("Ctrl+Shift+A"))
        select_type_act.triggered.connect(self._select_all_current_type)
        edit_menu.addAction(select_type_act)
        self._text_only_actions.append(select_type_act)

        delete_type_act = QAction("Delete All Current Event &Type", self)
        delete_type_act.triggered.connect(self._delete_all_current_type)
        edit_menu.addAction(delete_type_act)

        self._filter_type_act = QAction("Show &Only Current Event Type", self)
        self._filter_type_act.setCheckable(True)
        self._filter_type_act.setShortcut(QKeySequence("Ctrl+Shift+F"))
        self._filter_type_act.toggled.connect(self._toggle_filter_event_type)
        edit_menu.addAction(self._filter_type_act)
        self._text_only_actions.append(self._filter_type_act)

        # View
        view_menu = mb.addMenu("&View")

        self._view_action_group = QActionGroup(self)
        self._view_action_group.setExclusive(True)

        self._block_view_act = QAction("&Block View", self)
        self._block_view_act.setShortcut(QKeySequence("Ctrl+1"))
        self._block_view_act.setCheckable(True)
        self._block_view_act.setChecked(self._settings.get("mode_view", 0) == 0)
        self._block_view_act.triggered.connect(lambda: self._switch_view(0))
        self._view_action_group.addAction(self._block_view_act)
        view_menu.addAction(self._block_view_act)

        self._text_view_act = QAction("&Text View", self)
        self._text_view_act.setShortcut(QKeySequence("Ctrl+2"))
        self._text_view_act.setCheckable(True)
        self._text_view_act.setChecked(self._settings.get("mode_view", 0) == 1)
        self._text_view_act.triggered.connect(lambda: self._switch_view(1))
        self._view_action_group.addAction(self._text_view_act)
        view_menu.addAction(self._text_view_act)

        view_menu.addSeparator()

        # Text-only view actions (hidden in block mode)
        self._text_only_view_actions = []

        self._warn_action = QAction("Show &Warnings", self)
        self._warn_action.setCheckable(True)
        self._warn_action.setChecked(self._settings["show_warnings"])
        self._warn_action.toggled.connect(self._toggle_warnings)
        view_menu.addAction(self._warn_action)
        self._text_only_view_actions.append(self._warn_action)

        self._wrap_action = QAction("&Word Wrap", self)
        self._wrap_action.setCheckable(True)
        self._wrap_action.setChecked(self._settings.get("word_wrap", False))
        self._wrap_action.toggled.connect(self._toggle_word_wrap)
        view_menu.addAction(self._wrap_action)
        self._text_only_view_actions.append(self._wrap_action)

        self._connector_action = QAction("Show &Connectors", self)
        self._connector_action.setCheckable(True)
        self._connector_action.setChecked(self._settings.get("show_block_connectors", True))
        self._connector_action.toggled.connect(self._toggle_block_connectors)
        view_menu.addAction(self._connector_action)
        self._block_only_actions.append(self._connector_action)

        self._statusbar_action = QAction("Status &Bar", self)
        self._statusbar_action.setCheckable(True)
        self._statusbar_action.setChecked(self._settings.get("show_statusbar", True))
        self._statusbar_action.toggled.connect(self._toggle_statusbar)
        view_menu.addAction(self._statusbar_action)

        view_menu.addSeparator()

        font_act = QAction("Change &Font...", self)
        font_act.triggered.connect(self._change_font)
        view_menu.addAction(font_act)
        self._text_only_view_actions.append(font_act)

        zoom_in = QAction("Zoom &In", self)
        zoom_in.setShortcut(QKeySequence("Ctrl++"))
        zoom_in.triggered.connect(self._zoom_in)
        view_menu.addAction(zoom_in)

        zoom_out = QAction("Zoom &Out", self)
        zoom_out.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out.triggered.connect(self._zoom_out)
        view_menu.addAction(zoom_out)

        reset_zoom = QAction("Reset &Zoom", self)
        reset_zoom.setShortcut(QKeySequence("Ctrl+0"))
        reset_zoom.triggered.connect(self._reset_zoom)
        view_menu.addAction(reset_zoom)

        view_menu.addSeparator()

        reset_view = QAction("&Reset View Defaults", self)
        reset_view.triggered.connect(self._reset_view)
        view_menu.addAction(reset_view)

    def _create_toolbar(self):
        tb = QToolBar("Main Toolbar")
        tb.setMovable(False)
        self.addToolBar(tb)
        tb.addAction("Open .bin", self._open_bin)
        tb.addAction("Open .txt", self._open_txt)
        tb.addSeparator()
        tb.addAction("Close", self._close_file)
        tb.addSeparator()
        tb.addAction("Save .txt", self._save_txt)
        tb.addAction("Build .bin", self._build_bin)
        tb.addSeparator()
        tb.addAction(self._undo_action)
        tb.addAction(self._redo_action)
        tb.addSeparator()

        # View switch buttons
        self._view_button_group = QButtonGroup(self)
        self._view_button_group.setExclusive(True)

        self._tb_block = QToolButton()
        self._tb_block.setText("Block View")
        self._tb_block.setCheckable(True)
        self._tb_block.setChecked(self._settings.get("mode_view", 0) == 0)
        self._tb_block.setToolTip("Block View (Ctrl+1)")
        self._tb_block.clicked.connect(lambda: self._switch_view(0))
        self._view_button_group.addButton(self._tb_block)
        tb.addWidget(self._tb_block)

        self._tb_text = QToolButton()
        self._tb_text.setText("Text View")
        self._tb_text.setCheckable(True)
        self._tb_text.setChecked(self._settings.get("mode_view", 0) == 1)
        self._tb_text.setToolTip("Text View (Ctrl+2)")
        self._tb_text.clicked.connect(lambda: self._switch_view(1))
        self._view_button_group.addButton(self._tb_text)
        tb.addWidget(self._tb_text)

    #
    # File I/O
    #

    def _last_dir(self) -> str:
        return self._settings.get("last_directory", "") or ""

    def _remember_dir(self, path: str):
        self._settings["last_directory"] = os.path.dirname(path)

    def _check_dirty_before_open(self) -> bool:
        """Returns True if OK to proceed, False if cancelled."""
        if self.model.dirty or self._text_dirty:
            ret = self._ask_save("You have unsaved changes. Save before opening a new file?")
            if ret == QMessageBox.Save:
                self._save_txt()
            elif ret == QMessageBox.Cancel:
                return False
        return True

    def _open_bin(self):
        if not self._check_dirty_before_open():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Binary Script", self._last_dir(),
            "Binary Files (*.bin);;All Files (*)"
        )
        if not path:
            return
        try:
            entries = self._parse_bin(path)
            self._remember_dir(path)
            self._display_path = path
            self.model.filepath = os.path.splitext(path)[0] + ".txt"
            self.model.set_entries(entries)
            self._text_dirty = False
            self._update_title()
            self._status_label.setText(f"Opened: {os.path.basename(path)}")
        except Exception as e:
            self._show_error("Error", f"Failed to open binary:\n{e}")

    def _open_txt(self):
        if not self._check_dirty_before_open():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Text Script", self._last_dir(),
            "Text Files (*.txt);;All Files (*)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            self._remember_dir(path)
            self._display_path = path
            self.model.filepath = path
            self.model.from_text(text)
            self._text_dirty = False
            self._update_title()
            self._status_label.setText(f"Opened: {os.path.basename(path)}")
        except Exception as e:
            self._show_error("Error", f"Failed to open text:\n{e}")

    def _close_file(self):
        if self.model.count() == 0 and not self.text_view.toPlainText().strip():
            return
        if self.model.dirty or self._text_dirty:
            ret = self._ask_save("Save before closing?")
            if ret == QMessageBox.Save:
                self._save_txt()
            elif ret == QMessageBox.Cancel:
                return

        self._syncing = True
        self.text_view.blockSignals(True)
        self.text_view.setPlainText("")
        self.text_view.blockSignals(False)
        self._syncing = False
        self.model.set_entries([])
        self._display_path = None
        self.model.filepath = None
        self._text_dirty = False
        self.prop_panel.clear_selection()
        self._update_title()
        self._entry_count_label.setText("")
        self._status_label.setText("Ready")

    def _save_txt(self):
        if not self.model.filepath:
            self._save_txt_as()
            return
        self._do_save_txt(self.model.filepath)

    def _save_txt_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Text Script",
            self.model.filepath or self._last_dir(),
            "Text Files (*.txt);;All Files (*)"
        )
        if not path:
            return
        self._remember_dir(path)
        self.model.filepath = path
        self._display_path = path
        self._do_save_txt(path)

    def _do_save_txt(self, path: str):
        try:
            self._parse_text_to_model()
            text = self.model.to_text()
            with open(path, "w", encoding="utf-8") as f:
                f.write(text + "\n")
            self.model.undo_stack.setClean()
            self._text_dirty = False
            self._update_title()
            self._status_label.setText(f"Saved: {os.path.basename(path)}")
        except Exception as e:
            self._show_error("Error", f"Failed to save:\n{e}")

    def _build_bin(self):
        default = ""
        if self.model.filepath:
            default = os.path.splitext(self.model.filepath)[0] + ".bin"
        elif self._display_path:
            default = os.path.splitext(self._display_path)[0] + ".bin"
        else:
            default = self._last_dir()
        path, _ = QFileDialog.getSaveFileName(
            self, "Build Binary Script", default,
            "Binary Files (*.bin);;All Files (*)"
        )
        if not path:
            return
        try:
            self._remember_dir(path)
            self._parse_text_to_model()
            entries = self.model.entries()
            with open(path, "wb") as f:
                f.write(struct.pack("<4i", len(entries), 0, 0, 0))
                for entry in entries:
                    values = [entry.event_type] + list(entry.params)
                    f.write(struct.pack("<12i", *values))
            self._status_label.setText(f"Built: {os.path.basename(path)} ({len(entries)} entries)")
        except Exception as e:
            self._show_error("Error", f"Failed to build binary:\n{e}")

    def _parse_bin(self, path: str) -> list[ScriptEntry]:
        entries = []
        with open(path, "rb") as f:
            header = f.read(16)
            num_entries = struct.unpack("<i", header[:4])[0]
            for _ in range(num_entries):
                block = f.read(48)
                values = struct.unpack("<12i", block)
                entries.append(ScriptEntry(values[0], list(values[1:])))
        return entries

    #
    # Dialogs (properly styled to avoid dark-theme bleed)
    #

    def _show_error(self, title: str, text: str):
        msg = QMessageBox(QMessageBox.Critical, title, text, QMessageBox.Ok, self)
        msg.setStyleSheet("")  # Clear inherited dark styles
        msg.exec()

    def _ask_save(self, text: str) -> int:
        msg = QMessageBox(self)
        msg.setWindowTitle("Unsaved Changes")
        msg.setText(text)
        msg.setIcon(QMessageBox.Warning)
        msg.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        msg.setStyleSheet("")  # Clear inherited dark styles
        return msg.exec()

    #
    # Model <-> Text Sync
    #

    def _sync_model_to_text(self, *_args):
        if self._syncing:
            return
        self._syncing = True

        cursor_line = self.text_view.textCursor().blockNumber()
        text = self.model.to_text()

        self.text_view.blockSignals(True)
        self.text_view.setPlainText(text)
        self.text_view.document().clearUndoRedoStacks()
        self.text_view.blockSignals(False)

        target_line = min(cursor_line, self.text_view.document().blockCount() - 1)
        block = self.text_view.document().findBlockByNumber(max(0, target_line))
        if block.isValid():
            cursor = self.text_view.textCursor()
            cursor.setPosition(block.position())
            self.text_view.setTextCursor(cursor)

        self._update_flow_info()
        self._entry_count_label.setText(f"{self.model.count()} entries")
        self._text_dirty = False

        # Rebuild block view if it's the active view
        if self._current_view == 0:
            self.block_view.rebuild()

        self._syncing = False

    def _on_entry_modified(self, idx: int):
        if self._syncing:
            return
        self._syncing = True

        # Update text view
        entry = self.model.entry(idx)
        new_line = entry.to_text_line(idx)
        doc = self.text_view.document()
        block = doc.findBlockByNumber(idx)

        if block.isValid():
            cursor = QTextCursor(block)
            cursor.movePosition(QTextCursor.StartOfBlock)
            cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
            self.text_view.blockSignals(True)
            cursor.insertText(new_line)
            self.text_view.blockSignals(False)

        self._update_flow_info()

        # Update block view (refresh summary without full rebuild)
        self.block_view.refresh_block(idx)

        self._syncing = False

    def _on_text_changed(self):
        if self._syncing:
            return
        self._text_dirty = True
        self._update_title()

    def _parse_text_to_model(self):
        if not self._text_dirty:
            return
        text = self.text_view.toPlainText()
        self._syncing = True
        self.model.from_text(text)
        self._syncing = False
        self._text_dirty = False

    def _update_flow_info(self):
        entries = self.model.entries()
        flow_info = analyze_control_flow(entries)
        self.text_view.set_flow_info(flow_info)

    #
    # Line Selection -> Property Panel
    #

    def _on_line_clicked(self, line_idx: int):
        if 0 <= line_idx < self.model.count():
            # When filter is active, ignore clicks on hidden entries
            if self._filter_active_type is not None:
                block = self.text_view.document().findBlockByNumber(line_idx)
                if block.isValid() and not block.isVisible():
                    # Snap cursor back to the nearest visible block
                    for offset in range(1, self.model.count()):
                        for candidate in (line_idx - offset, line_idx + offset):
                            if 0 <= candidate < self.model.count():
                                b = self.text_view.document().findBlockByNumber(candidate)
                                if b.isValid() and b.isVisible():
                                    self.text_view.highlight_entry(candidate)
                                    return
                    return

            self.prop_panel.set_selected_entry(line_idx)
            entry = self.model.entry(line_idx)
            et = entry.event_type
            count = sum(1 for e in self.model.entries() if e.event_type == et)
            name = entry.name
            self._type_count_label.setText(
                f"{name}: {count} instance{'s' if count != 1 else ''}"
            )
        else:
            # Clicked beyond the last entry - ignore when filter is active
            if self._filter_active_type is not None:
                return
            self.prop_panel.clear_selection()
            self._type_count_label.setText("")

    def _on_param_changed(self, entry_idx: int, param_idx: int, value: int):
        self.model.set_param(entry_idx, param_idx, value)

    #
    # Entry Manipulation
    #

    def _current_line(self) -> int:
        if self._current_view == 0:
            return self.block_view._selected_index
        return self.text_view.textCursor().blockNumber()

    def _insert_before(self):
        idx = max(0, self._current_line())
        self.model.insert_entry(idx)
        if self._current_view == 1:
            self.text_view.highlight_entry(idx)
        else:
            self.block_view._selected_index = idx

    def _insert_after(self):
        idx = min(self._current_line() + 1, self.model.count())
        self.model.insert_entry(idx)
        if self._current_view == 1:
            self.text_view.highlight_entry(idx)
        else:
            self.block_view._selected_index = idx

    def _delete_entry(self):
        idx = self._current_line()
        if 0 <= idx < self.model.count():
            self.model.remove_entry(idx)
            new_idx = min(idx, self.model.count() - 1)
            if new_idx >= 0:
                if self._current_view == 1:
                    self.text_view.highlight_entry(new_idx)
                else:
                    self.block_view._selected_index = new_idx
                    self.block_view.highlight_entry(new_idx)
                self.prop_panel.set_selected_entry(new_idx)
            else:
                self.prop_panel.clear_selection()

    def _duplicate_entry(self):
        idx = self._current_line()
        if 0 <= idx < self.model.count():
            clone = self.model.entry(idx).clone()
            self.model.insert_entry(idx + 1, clone)
            if self._current_view == 1:
                self.text_view.highlight_entry(idx + 1)
            else:
                self.block_view._selected_index = idx + 1

    def _move_up(self):
        idx = self._current_line()
        if 0 < idx < self.model.count():
            self.model.move_entry(idx, idx - 1)
            if self._current_view == 1:
                self.text_view.highlight_entry(idx - 1)
            else:
                self.block_view._selected_index = idx - 1
                self.block_view.highlight_entry(idx - 1)
            self.prop_panel.set_selected_entry(idx - 1)

    def _move_down(self):
        idx = self._current_line()
        if 0 <= idx < self.model.count() - 1:
            self.model.move_entry(idx, idx + 1)
            if self._current_view == 1:
                self.text_view.highlight_entry(idx + 1)
            else:
                self.block_view._selected_index = idx + 1
                self.block_view.highlight_entry(idx + 1)
            self.prop_panel.set_selected_entry(idx + 1)

    def _reindex(self):
        self._parse_text_to_model()
        self._sync_model_to_text()
        self._status_label.setText("Re-indexed all entries")

    def _open_find(self):
        self.find_bar.open_find()

    def _open_find_replace(self):
        self.find_bar.open_find_replace()

    def _switch_view(self, index: int):
        """Switch between block view (0) and text view (1)."""
        if index == self._current_view:
            return

        if index == 0:
            # Switching TO block view: parse pending text edits, close find bar
            self._parse_text_to_model()
            if self.find_bar.isVisible():
                self.find_bar.close_bar()
            self.block_view.rebuild()

        self._view_stack.setCurrentIndex(index)
        self._current_view = index
        self._settings["mode_view"] = index

        # Update check states
        self._block_view_act.setChecked(index == 0)
        self._text_view_act.setChecked(index == 1)
        self._tb_block.setChecked(index == 0)
        self._tb_text.setChecked(index == 1)

        # Toggle text-only and block-only menu items
        is_text = (index == 1)
        for act in self._text_only_actions:
            act.setVisible(is_text)
        for act in self._text_only_view_actions:
            act.setVisible(is_text)
        for act in self._block_only_actions:
            act.setVisible(not is_text)

        self._update_zoom_label()
        self._status_label.setText("Block View" if index == 0 else "Text View")

    def _on_block_clicked(self, entry_idx: int):
        """Handle click/navigation on a block in the block view."""
        if 0 <= entry_idx < self.model.count():
            self.prop_panel.set_selected_entry(entry_idx)
            entry = self.model.entry(entry_idx)
            et = entry.event_type
            # Find position among same-type entries
            same_type = [i for i, e in enumerate(self.model.entries()) if e.event_type == et]
            pos = same_type.index(entry_idx) + 1 if entry_idx in same_type else 0
            total = len(same_type)
            name = entry.name
            self._type_count_label.setText(
                f"{name}: {pos}/{total} (Alt+←→ to jump)"
            )

    def _on_block_param_changed(self, entry_idx: int, param_idx: int, value: int):
        """Handle inline param edit from block view."""
        self.model.set_param(entry_idx, param_idx, value)
        # Also update property panel if it's showing this entry
        if self.prop_panel._current_idx == entry_idx:
            self.prop_panel.set_selected_entry(entry_idx)

    def _on_block_entry_moved(self, from_idx: int, to_idx: int):
        """Handle drag-to-reorder from block view."""
        self.model.move_entry(from_idx, to_idx)
        # Select the moved entry at its new position
        self.block_view.highlight_entry(to_idx)
        self.block_view._selected_index = to_idx
        self.prop_panel.set_selected_entry(to_idx)
        self._status_label.setText(f"Moved entry #{from_idx} → #{to_idx}")

    def _on_find_status(self, message: str):
        self._status_label.setText(message)

    def _do_undo(self):
        """Route undo to the right place: text editor if text was edited directly, model otherwise."""
        if self._text_dirty or self.find_bar.isVisible():
            self.text_view.undo()
            # Re-run find if bar is open
            if self.find_bar.isVisible():
                self.find_bar._do_search()
        else:
            self.model.undo_stack.undo()

    def _do_redo(self):
        if self._text_dirty or self.find_bar.isVisible():
            self.text_view.redo()
            if self.find_bar.isVisible():
                self.find_bar._do_search()
        else:
            self.model.undo_stack.redo()

    def _update_undo_state(self, *_args):
        """Enable/disable undo/redo actions based on both stacks."""
        can_undo = (
            self.model.undo_stack.canUndo()
            or self.text_view.document().isUndoAvailable()
        )
        can_redo = (
            self.model.undo_stack.canRedo()
            or self.text_view.document().isRedoAvailable()
        )
        self._undo_action.setEnabled(can_undo)
        self._redo_action.setEnabled(can_redo)

    #
    # View
    #

    def _toggle_warnings(self, checked: bool):
        self.text_view.show_warnings = checked
        self._settings["show_warnings"] = checked

    def _toggle_word_wrap(self, checked: bool):
        if checked:
            self.text_view.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        else:
            self.text_view.setLineWrapMode(QPlainTextEdit.NoWrap)
        self._settings["word_wrap"] = checked

    def _toggle_block_connectors(self, checked: bool):
        self._settings["show_block_connectors"] = checked
        self.block_view.set_show_connectors(checked)

    def _toggle_statusbar(self, checked: bool):
        self._status.setVisible(checked)
        self._settings["show_statusbar"] = checked

    def _zoom_in(self):
        if self._current_view == 1:
            self.text_view.zoomIn(1)
            self._settings["zoom_delta"] = self._settings.get("zoom_delta", 0) + 1
        else:
            self.block_view.scale(1.1, 1.1)
            self._settings["block_zoom_delta"] = self._settings.get("block_zoom_delta", 0) + 1
        self._update_zoom_label()

    def _zoom_out(self):
        if self._current_view == 1:
            self.text_view.zoomOut(1)
            self._settings["zoom_delta"] = self._settings.get("zoom_delta", 0) - 1
        else:
            self.block_view.scale(0.9, 0.9)
            self._settings["block_zoom_delta"] = self._settings.get("block_zoom_delta", 0) - 1
        self._update_zoom_label()

    def _reset_zoom(self):
        if self._current_view == 1:
            delta = self._settings.get("zoom_delta", 0)
            if delta > 0:
                self.text_view.zoomOut(delta)
            elif delta < 0:
                self.text_view.zoomIn(-delta)
            self._settings["zoom_delta"] = 0
        else:
            self.block_view.resetTransform()
            self._settings["block_zoom_delta"] = 0
        self._update_zoom_label()
        self._status_label.setText("Zoom reset to 100%")

    def _update_zoom_label(self):
        if self._current_view == 1:
            delta = self._settings.get("zoom_delta", 0)
            pct = 100 + delta * 10
        else:
            delta = self._settings.get("block_zoom_delta", 0)
            pct = round(100 * (1.1 ** delta))
        self._zoom_label.setText(f"{pct}%")

    def _change_font(self):
        dlg = QFontDialog(self.text_view.font(), self)
        dlg.setStyleSheet("")
        if dlg.exec():
            font = dlg.selectedFont()
            self.text_view.setFont(font)
            self._settings["font_family"] = font.family()
            self._settings["font_size"] = font.pointSize()
            self._settings["zoom_delta"] = 0
            self._update_zoom_label()

    def _reset_view(self):
        font = QFont(DEFAULT_SETTINGS["font_family"], DEFAULT_SETTINGS["font_size"])
        self.text_view.setFont(font)
        self.text_view.show_warnings = DEFAULT_SETTINGS["show_warnings"]
        self._warn_action.setChecked(DEFAULT_SETTINGS["show_warnings"])
        self._wrap_action.setChecked(False)
        self._statusbar_action.setChecked(True)
        self._settings["font_family"] = DEFAULT_SETTINGS["font_family"]
        self._settings["font_size"] = DEFAULT_SETTINGS["font_size"]
        self._settings["zoom_delta"] = 0
        self._update_zoom_label()
        self._status_label.setText("View reset to defaults")

    #
    # Go To / Selection / Filter
    #

    def _delete_selection(self):
        cursor = self.text_view.textCursor()
        if cursor.hasSelection():
            cursor.removeSelectedText()

    def _go_to_entry(self):
        max_entry = self.model.count() - 1
        if max_entry < 0:
            self._status_label.setText("No entries to jump to")
            return
        dlg = QInputDialog(self)
        dlg.setWindowTitle("Go to Entry")
        dlg.setLabelText(f"Entry number (0–{max_entry}):")
        dlg.setIntRange(0, max_entry)
        dlg.setIntValue(self._current_line())
        dlg.setStyleSheet("")
        if dlg.exec():
            idx = dlg.intValue()
            if self._current_view == 1:
                self.text_view.highlight_entry(idx)
            else:
                self.block_view.highlight_entry(idx)
                self.block_view._selected_index = idx
            self.prop_panel.set_selected_entry(idx)
            self._status_label.setText(f"Jumped to entry #{idx}")

    def _navigate_same_type(self, direction: int):
        """Jump to next/previous entry of the same event type. Works in both views."""
        idx = self._current_line()
        if idx < 0 or idx >= self.model.count():
            return
        target_type = self.model.entry(idx).event_type
        count = self.model.count()
        i = idx + direction
        while 0 <= i < count:
            if self.model.entry(i).event_type == target_type:
                if self._current_view == 1:
                    self.text_view.highlight_entry(i)
                else:
                    self.block_view.highlight_entry(i)
                    self.block_view._selected_index = i
                    self.block_view._scene.update_connector_highlights(i)
                self.prop_panel.set_selected_entry(i)
                self._on_line_clicked(i) if self._current_view == 1 else self._on_block_clicked(i)
                return
            i += direction
        self._status_label.setText("No more matches in that direction")

    def _selected_entry_index(self) -> int:
        """Return the property panel's selected entry, falling back to cursor line."""
        idx = self.prop_panel._current_idx
        if 0 <= idx < self.model.count():
            return idx
        return self._current_line()

    def _select_all_current_type(self):
        """Copy all complete lines matching the current event type to clipboard and highlight them."""
        idx = self._selected_entry_index()
        if idx < 0 or idx >= self.model.count():
            return
        target_type = self.model.entry(idx).event_type
        target_name = self.model.entry(idx).name

        # Collect matching lines and highlight them
        matching_lines = []
        from PySide6.QtWidgets import QTextEdit
        from PySide6.QtGui import QTextCharFormat, QColor, QTextCursor

        highlight_fmt = QTextCharFormat()
        highlight_fmt.setBackground(QColor("#264F78"))  # Blue selection-like highlight
        highlight_fmt.setProperty(0x10001, True)  # Tag for cleanup

        # Clear previous type-select highlights
        base = [s for s in self.text_view.extraSelections() if not s.format.property(0x10001)]
        new_sels = []

        doc = self.text_view.document()
        for i, entry in enumerate(self.model.entries()):
            if entry.event_type == target_type:
                matching_lines.append(entry.to_text_line(i))
                # Highlight the full line
                block = doc.findBlockByNumber(i)
                if block.isValid():
                    sel = QTextEdit.ExtraSelection()
                    sel.format = highlight_fmt
                    sel.format.setProperty(QTextFormat.FullWidthSelection, True)
                    sel.cursor = QTextCursor(block)
                    sel.cursor.clearSelection()
                    new_sels.append(sel)

        self.text_view.setExtraSelections(base + new_sels)

        # Copy to clipboard (optional)
        #if matching_lines:
        #    clipboard_text = "\n".join(matching_lines)
        #    QApplication.clipboard().setText(clipboard_text)

        #count = len(matching_lines)
        #self._status_label.setText(
        #    f"Copied {count} {target_name} line{'s' if count != 1 else ''} to clipboard"
        #)

    _filter_active_type: int | None = None

    def _toggle_filter_event_type(self, checked: bool):
        """Show/hide lines that don't match the current event type."""
        if checked:
            idx = self._selected_entry_index()
            if idx < 0 or idx >= self.model.count():
                self._filter_type_act.setChecked(False)
                return
            target_type = self.model.entry(idx).event_type
            self._filter_active_type = target_type
            target_name = self.model.entry(idx).name

            # Hide non-matching blocks using model data (not text matching)
            doc = self.text_view.document()
            visible_count = 0
            for i in range(self.model.count()):
                block = doc.findBlockByNumber(i)
                if block.isValid():
                    matches = self.model.entry(i).event_type == target_type
                    block.setVisible(matches)
                    if matches:
                        visible_count += 1
            # Hide any extra blocks beyond entry count
            for i in range(self.model.count(), doc.blockCount()):
                block = doc.findBlockByNumber(i)
                if block.isValid():
                    block.setVisible(False)

            doc.markContentsDirty(0, doc.characterCount())
            self.text_view.viewport().update()
            self._status_label.setText(
                f"Filtered: showing {visible_count} {target_name} entries (Ctrl+Shift+F to restore)"
            )
        else:
            self._filter_active_type = None
            doc = self.text_view.document()
            block = doc.begin()
            while block.isValid():
                block.setVisible(True)
                block = block.next()
            doc.markContentsDirty(0, doc.characterCount())
            self.text_view.viewport().update()
            self._status_label.setText("Filter cleared - all entries visible")

    def _delete_all_current_type(self):
        """Remove all entries matching the currently selected event type."""
        idx = self._selected_entry_index()
        if idx < 0 or idx >= self.model.count():
            return
        target_type = self.model.entry(idx).event_type
        target_name = self.model.entry(idx).name
        count = sum(1 for e in self.model.entries() if e.event_type == target_type)

        msg = QMessageBox(self)
        msg.setWindowTitle("Delete All Event Type")
        msg.setText(
            f"Delete all {count} {target_name} (type {target_type}) entries?"
        )
        msg.setIcon(QMessageBox.Warning)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setStyleSheet("")
        if msg.exec() != QMessageBox.Yes:
            return

        # Remove matching entries as a single undo operation
        indices = [i for i, e in enumerate(self.model.entries()) if e.event_type == target_type]
        self.model.undo_stack.beginMacro(f"Delete all {target_name}")
        for i in reversed(indices):
            self.model.remove_entry(i)
        self.model.undo_stack.endMacro()

        self.prop_panel.clear_selection()
        self._status_label.setText(f"Deleted {count} {target_name} entries")

    def _update_title(self, *_args):
        if self._display_path:
            name = os.path.basename(self._display_path)
        elif self.model.filepath:
            name = os.path.basename(self.model.filepath)
        else:
            name = "Untitled"
        dirty = " •" if (self.model.dirty or self._text_dirty) else ""
        self.setWindowTitle(f"{name}{dirty} - FE3H Event Script Editor")

    #
    # Theme (scoped to avoid bleeding into system dialogs)
    #

    def _apply_dark_theme(self):
        # Only style the main window and its known children, not generic Qt classes
        self.setStyleSheet("""
            QMainWindow { background-color: #21252B; }
            QMainWindow > QMenuBar { background-color: #21252B; color: #ABB2BF; }
            QMenuBar::item:selected { background-color: #2C313A; }
            QMenu { background-color: #282C34; color: #ABB2BF; border: 1px solid #3E4451; }
            QMenu::item:selected { background-color: #3E4451; }
            QToolBar { background-color: #21252B; border: none; spacing: 4px; padding: 2px; }
            QToolBar QToolButton { color: #ABB2BF; padding: 4px 8px; border-radius: 3px; }
            QToolBar QToolButton:hover { background-color: #2C313A; }
            QDockWidget { color: #ABB2BF; titlebar-close-icon: none; }
            QDockWidget::title {
                background-color: #21252B; padding: 6px;
                border-bottom: 1px solid #3E4451;
            }
            QWidget#prop_panel_root {
                background-color: #21252B;
            }
            QWidget#prop_panel_root QGroupBox {
                color: #ABB2BF; border: 1px solid #3E4451; border-radius: 4px;
                margin-top: 8px; padding-top: 12px;
                background-color: #282C34;
            }
            QWidget#prop_panel_root QGroupBox::title {
                subcontrol-origin: margin; left: 10px; padding: 0 4px;
            }
            QWidget#prop_panel_root QLabel { color: #ABB2BF; }
            QWidget#prop_panel_root QComboBox {
                background-color: #282C34; color: #ABB2BF;
                border: 1px solid #3E4451; border-radius: 3px; padding: 4px;
            }
            QWidget#prop_panel_root QComboBox:hover { border-color: #528BFF; }
            QWidget#prop_panel_root QComboBox QAbstractItemView {
                background-color: #282C34; color: #ABB2BF;
                selection-background-color: #3E4451;
            }
            QWidget#prop_panel_root QComboBox QLineEdit {
                background-color: #282C34; color: #ABB2BF;
                border: none; padding: 0px;
            }
            QWidget#prop_panel_root QSpinBox {
                background-color: #282C34; color: #ABB2BF;
                border: 1px solid #3E4451; border-radius: 3px; padding: 4px;
            }
            QWidget#prop_panel_root QSpinBox:hover { border-color: #528BFF; }
            QWidget#prop_panel_root QScrollArea { background-color: #21252B; border: none; }
            QWidget#prop_panel_root QScrollArea > QWidget > QWidget { background-color: #21252B; }
            QScrollBar:vertical {
                background-color: #21252B; width: 10px; border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #3E4451; border-radius: 5px; min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background-color: #495162; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar:horizontal {
                background-color: #21252B; height: 10px; border: none;
            }
            QScrollBar::handle:horizontal {
                background-color: #3E4451; border-radius: 5px; min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover { background-color: #495162; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
            QStatusBar { background-color: #21252B; color: #5C6370; }
            QStatusBar QLabel { color: #5C6370; }
        """)

    #
    # Lifecycle
    #

    def closeEvent(self, event):
        if self.model.dirty or self._text_dirty:
            ret = self._ask_save("You have unsaved changes. Save before closing?")
            if ret == QMessageBox.Save:
                self._save_txt()
                event.accept()
            elif ret == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
                return
        else:
            event.accept()

        # Save settings
        self._settings["window_maximized"] = self.isMaximized()

        # Use normalGeometry so we save the un-maximized dimensions
        # (prevents the window from getting stuck at full-screen resolution)
        normal_geo = self.normalGeometry()
        self._settings["window_width"] = normal_geo.width()
        self._settings["window_height"] = normal_geo.height()

        save_settings(self._settings)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("FE3H Event Script Editor")
    app.setOrganizationName("FE3H-RE")

    window = MainWindow()
    if window._settings.get("window_maximized", False):
        window.showMaximized()
    else:
        window.show()

    if len(sys.argv) > 1:
        path = sys.argv[1]
        if path.endswith(".bin"):
            try:
                entries = window._parse_bin(path)
                window._display_path = path
                window.model.filepath = os.path.splitext(path)[0] + ".txt"
                window.model.set_entries(entries)
                window._update_title()
            except Exception as e:
                print(f"Error opening {path}: {e}")
        elif path.endswith(".txt"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                window._display_path = path
                window.model.filepath = path
                window.model.from_text(text)
                window._update_title()
            except Exception as e:
                print(f"Error opening {path}: {e}")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
