"""
FE3H Event Script Editor - Find & Replace
Embedded bar at the top of the text view.
"""

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton,
    QCheckBox, QLabel, QSpinBox, QTextEdit
)
from PySide6.QtGui import QTextCursor, QTextDocument, QColor, QTextCharFormat


class FindLineEdit(QLineEdit):
    """QLineEdit that forwards Esc/F3 to the find bar."""
    def __init__(self, bar, parent=None):
        super().__init__(parent)
        self._bar = bar

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._bar.close_bar()
            return
        if event.key() == Qt.Key_F3:
            if event.modifiers() & Qt.ShiftModifier:
                self._bar._find_prev()
            else:
                self._bar._find_next()
            return
        super().keyPressEvent(event)


class FindReplaceBar(QWidget):
    closed = Signal()
    status_message = Signal(str)  # Sends feedback to the status bar

    # Max highlights to avoid lag on large files
    MAX_HIGHLIGHTS = 500

    def __init__(self, text_view, parent=None):
        super().__init__(parent)
        self.text_view = text_view
        self._matches = []
        self._current_match = -1

        # Debounce timer for live search
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(150)
        self._search_timer.timeout.connect(self._do_search)

        self.setObjectName("find_replace_bar")
        self.setStyleSheet("""
            #find_replace_bar {
                background-color: #2C313A;
                border-bottom: 1px solid #3E4451;
                padding: 4px;
            }
            #find_replace_bar QLineEdit {
                background-color: #282C34; color: #ABB2BF;
                border: 1px solid #3E4451; border-radius: 3px;
                padding: 4px 6px; min-width: 200px;
            }
            #find_replace_bar QLineEdit:focus { border-color: #528BFF; }
            #find_replace_bar QPushButton {
                background-color: #3E4451; color: #ABB2BF;
                border: 1px solid #4B5263; border-radius: 3px;
                padding: 4px 10px; min-width: 28px;
            }
            #find_replace_bar QPushButton:hover { background-color: #4B5263; }
            #find_replace_bar QPushButton:pressed { background-color: #528BFF; }
            #find_replace_bar QPushButton#close_btn {
                min-width: 20px; max-width: 24px; padding: 2px;
                font-weight: bold; font-size: 14px;
            }
            #find_replace_bar QCheckBox { color: #ABB2BF; spacing: 4px; }
            #find_replace_bar QCheckBox::indicator {
                width: 14px; height: 14px;
                border: 1px solid #3E4451; border-radius: 2px;
                background-color: #282C34;
            }
            #find_replace_bar QCheckBox::indicator:checked {
                background-color: #528BFF; border-color: #528BFF;
            }
            #find_replace_bar QLabel { color: #ABB2BF; }
            #find_replace_bar QSpinBox {
                background-color: #282C34; color: #ABB2BF;
                border: 1px solid #3E4451; border-radius: 3px;
                padding: 2px 4px; max-width: 60px;
            }
        """)

        self._build_ui()
        self.hide()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 4, 6, 4)
        outer.setSpacing(4)

        # Row 1: Find
        find_row = QHBoxLayout()
        find_row.setSpacing(4)

        self._find_input = FindLineEdit(self)
        self._find_input.setPlaceholderText("Find...")
        self._find_input.textChanged.connect(self._on_find_text_changed)
        self._find_input.returnPressed.connect(self._find_next)
        find_row.addWidget(self._find_input, stretch=1)

        # Next first, then Previous (more common to search forward)
        self._btn_next = QPushButton("▼ Next")
        self._btn_next.setToolTip("Find Next (F3)")
        self._btn_next.clicked.connect(self._find_next)
        find_row.addWidget(self._btn_next)

        self._btn_prev = QPushButton("▲ Prev")
        self._btn_prev.setToolTip("Find Previous (Shift+F3)")
        self._btn_prev.clicked.connect(self._find_prev)
        find_row.addWidget(self._btn_prev)

        self._match_label = QLabel("")
        self._match_label.setMinimumWidth(80)
        find_row.addWidget(self._match_label)

        find_row.addSpacing(8)

        self._chk_case = QCheckBox("Aa")
        self._chk_case.setToolTip("Match Case")
        self._chk_case.toggled.connect(self._on_options_changed)
        find_row.addWidget(self._chk_case)

        self._chk_word = QCheckBox("W")
        self._chk_word.setToolTip("Whole Word Only")
        self._chk_word.toggled.connect(self._on_options_changed)
        find_row.addWidget(self._chk_word)

        find_row.addSpacing(8)

        self._close_btn = QPushButton("✕")
        self._close_btn.setObjectName("close_btn")
        self._close_btn.setToolTip("Close (Esc)")
        self._close_btn.clicked.connect(self.close_bar)
        find_row.addWidget(self._close_btn)

        outer.addLayout(find_row)

        # Row 2: Replace
        self._replace_row = QWidget()
        replace_layout = QHBoxLayout(self._replace_row)
        replace_layout.setContentsMargins(0, 0, 0, 0)
        replace_layout.setSpacing(4)

        self._replace_input = FindLineEdit(self)
        self._replace_input.setPlaceholderText("Replace with...")
        self._replace_input.returnPressed.connect(self._replace_current)
        replace_layout.addWidget(self._replace_input, stretch=1)

        self._btn_replace = QPushButton("Replace")
        self._btn_replace.setToolTip("Replace current match and find next")
        self._btn_replace.clicked.connect(self._replace_current)
        replace_layout.addWidget(self._btn_replace)

        self._btn_replace_all = QPushButton("Replace All")
        self._btn_replace_all.setToolTip("Replace all matches")
        self._btn_replace_all.clicked.connect(self._replace_all)
        replace_layout.addWidget(self._btn_replace_all)

        self._btn_replace_n = QPushButton("Replace N")
        self._btn_replace_n.setToolTip("Replace next N matches from cursor")
        self._btn_replace_n.clicked.connect(self._replace_n)
        replace_layout.addWidget(self._btn_replace_n)

        self._spin_n = QSpinBox()
        self._spin_n.setRange(1, 9999)
        self._spin_n.setValue(1)
        self._spin_n.setToolTip("Number of matches to replace")
        replace_layout.addWidget(self._spin_n)

        replace_layout.addSpacing(32)

        outer.addWidget(self._replace_row)

    #
    # Public API
    #

    def open_find(self):
        self._replace_row.hide()
        self.show()
        self._focus_and_select()

    def open_find_replace(self):
        self._replace_row.show()
        self.show()
        self._focus_and_select()

    def close_bar(self):
        self._clear_highlights()
        self._matches = []
        self._current_match = -1
        self._match_label.setText("")
        self.hide()
        self.text_view.setFocus()
        self.closed.emit()

    def _focus_and_select(self):
        self._find_input.setFocus()
        cursor = self.text_view.textCursor()
        if cursor.hasSelection():
            selected = cursor.selectedText()
            if "\u2029" not in selected:
                self._find_input.setText(selected)
        self._find_input.selectAll()
        # Immediate search (no debounce) on open
        self._do_search()

    #
    # Search Logic
    #

    def _build_flags(self) -> QTextDocument.FindFlags:
        flags = QTextDocument.FindFlags()
        if self._chk_case.isChecked():
            flags |= QTextDocument.FindCaseSensitively
        if self._chk_word.isChecked():
            flags |= QTextDocument.FindWholeWords
        return flags

    def _do_search(self):
        """Find all matches and highlight them."""
        self._clear_highlights()
        self._matches = []
        self._current_match = -1

        query = self._find_input.text()
        if not query:
            self._match_label.setText("")
            self._match_label.setStyleSheet("color: #ABB2BF;")
            return

        doc = self.text_view.document()
        flags = self._build_flags()

        cursor = QTextCursor(doc)
        cursor.movePosition(QTextCursor.Start)

        while True:
            found = doc.find(query, cursor, flags)
            if found.isNull() or not found.hasSelection():
                break
            self._matches.append((found.selectionStart(), found.selectionEnd()))
            cursor = found
            cursor.movePosition(QTextCursor.Right)

        if self._matches:
            # Jump to nearest match at or after cursor
            cur_pos = self.text_view.textCursor().position()
            best = 0
            for i, (start, end) in enumerate(self._matches):
                if start >= cur_pos:
                    best = i
                    break
            self._current_match = best
            self._apply_highlights()
            self._go_to_match(self._current_match)

        self._update_match_label()

    def _apply_highlights(self):
        """Highlight matches. Caps count for performance."""
        # Keep only non-find selections (current line highlight, block partners, etc.)
        base_selections = [
            s for s in self.text_view.extraSelections()
            if not s.format.property(0x10000)
        ]

        highlight_fmt = QTextCharFormat()
        highlight_fmt.setBackground(QColor("#5C4A1E"))
        highlight_fmt.setProperty(0x10000, True)

        current_fmt = QTextCharFormat()
        current_fmt.setBackground(QColor("#835E1A"))
        current_fmt.setProperty(0x10000, True)

        new_sels = []
        count = min(len(self._matches), self.MAX_HIGHLIGHTS)
        for i in range(count):
            start, end = self._matches[i]
            sel = QTextEdit.ExtraSelection()
            sel.format = current_fmt if i == self._current_match else highlight_fmt
            sel.cursor = QTextCursor(self.text_view.document())
            sel.cursor.setPosition(start)
            sel.cursor.setPosition(end, QTextCursor.KeepAnchor)
            new_sels.append(sel)

        self.text_view.setExtraSelections(base_selections + new_sels)

    def _clear_highlights(self):
        cleaned = [
            s for s in self.text_view.extraSelections()
            if not s.format.property(0x10000)
        ]
        self.text_view.setExtraSelections(cleaned)

    def _go_to_match(self, idx: int):
        if not self._matches or idx < 0 or idx >= len(self._matches):
            return
        start, end = self._matches[idx]
        cursor = self.text_view.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        self.text_view.setTextCursor(cursor)
        self.text_view.centerCursor()
        # Refresh highlight to show current match brighter
        self._apply_highlights()

    def _update_match_label(self):
        total = len(self._matches)
        if total == 0:
            if self._find_input.text():
                self._match_label.setText("No matches")
                self._match_label.setStyleSheet("color: #E06C75;")
                self.status_message.emit("No matches found")
            else:
                self._match_label.setText("")
                self._match_label.setStyleSheet("color: #ABB2BF;")
        else:
            idx = self._current_match + 1
            self._match_label.setText(f"{idx} of {total}")
            self._match_label.setStyleSheet("color: #98C379;")
            capped = " (highlighting capped)" if total > self.MAX_HIGHLIGHTS else ""
            self.status_message.emit(f"Found {total} matches{capped}")

    #
    # Navigation
    #

    def _find_next(self):
        if not self._matches:
            self._do_search()
            if not self._matches:
                self.status_message.emit("No matches found")
            return
        self._current_match = (self._current_match + 1) % len(self._matches)
        self._go_to_match(self._current_match)
        self._update_match_label()

    def _find_prev(self):
        if not self._matches:
            self._do_search()
            if not self._matches:
                self.status_message.emit("No matches found")
            return
        self._current_match = (self._current_match - 1) % len(self._matches)
        self._go_to_match(self._current_match)
        self._update_match_label()

    #
    # Replace
    #

    def _replace_current(self):
        """Replace the current match and advance to next."""
        if not self._matches:
            self._do_search()
            if not self._matches:
                self.status_message.emit("No matches to replace")
            return

        if self._current_match < 0:
            self._current_match = 0
            self._go_to_match(0)
            return

        start, end = self._matches[self._current_match]
        replacement = self._replace_input.text()

        cursor = QTextCursor(self.text_view.document())
        cursor.beginEditBlock()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        cursor.insertText(replacement)
        cursor.endEditBlock()

        self.text_view.document().setModified(True)
        self.status_message.emit("Replaced 1 match")

        # Re-search to update positions
        self._do_search()

    def _replace_all(self):
        if not self._matches:
            self._do_search()
            if not self._matches:
                self.status_message.emit("No matches to replace")
                return

        replacement = self._replace_input.text()
        count = len(self._matches)

        cursor = QTextCursor(self.text_view.document())
        cursor.beginEditBlock()
        for start, end in reversed(self._matches):
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.KeepAnchor)
            cursor.insertText(replacement)
        cursor.endEditBlock()

        self.text_view.document().setModified(True)
        self._do_search()

        self._match_label.setText(f"Replaced {count}")
        self._match_label.setStyleSheet("color: #98C379;")
        self.status_message.emit(f"Replaced all {count} matches")

    def _replace_n(self):
        if not self._matches:
            self._do_search()
            if not self._matches:
                self.status_message.emit("No matches to replace")
                return

        if self._current_match < 0:
            self._current_match = 0

        n = self._spin_n.value()
        replacement = self._replace_input.text()
        total = len(self._matches)

        # Gather indices from current position forward, wrapping
        indices = []
        for i in range(n):
            idx = (self._current_match + i) % total
            if idx in indices:
                break
            indices.append(idx)

        # Sort descending by position to avoid offset shifts
        positions = sorted(
            [(self._matches[idx], idx) for idx in indices],
            key=lambda x: x[0][0], reverse=True
        )

        cursor = QTextCursor(self.text_view.document())
        cursor.beginEditBlock()
        for (start, end), _ in positions:
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.KeepAnchor)
            cursor.insertText(replacement)
        cursor.endEditBlock()

        replaced = len(positions)
        self.text_view.document().setModified(True)
        self._do_search()

        self._match_label.setText(f"Replaced {replaced}")
        self._match_label.setStyleSheet("color: #98C379;")
        self.status_message.emit(f"Replaced {replaced} of {n} requested matches")

    #
    # Events
    #

    def _on_find_text_changed(self, _text):
        # Debounce: restart timer on each keystroke
        self._search_timer.start()

    def _on_options_changed(self, _checked):
        self._do_search()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close_bar()
        elif event.key() == Qt.Key_F3:
            if event.modifiers() & Qt.ShiftModifier:
                self._find_prev()
            else:
                self._find_next()
        else:
            super().keyPressEvent(event)
