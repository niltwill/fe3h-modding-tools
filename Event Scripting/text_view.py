"""
FE3H Event Script Editor - Text View
"""

import re
from PySide6.QtCore import Qt, QRect, QSize, Signal
from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PySide6.QtGui import (
    QColor, QFont, QPainter, QSyntaxHighlighter, QTextCharFormat,
    QTextFormat, QTextCursor, QPen, QBrush
)

from control_flow import FlowInfo, GROUP_COLORS


class EVScriptHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._fmt_index = QTextCharFormat()
        self._fmt_index.setForeground(QColor("#828997"))  # brighter grey

        self._fmt_event_name = QTextCharFormat()
        self._fmt_event_name.setForeground(QColor("#E06C75"))
        self._fmt_event_name.setFontWeight(QFont.Bold)

        self._fmt_control_flow = QTextCharFormat()
        self._fmt_control_flow.setForeground(QColor("#C678DD"))
        self._fmt_control_flow.setFontWeight(QFont.Bold)

        self._fmt_param_name = QTextCharFormat()
        self._fmt_param_name.setForeground(QColor("#61AFEF"))

        self._fmt_enum_value = QTextCharFormat()
        self._fmt_enum_value.setForeground(QColor("#98C379"))

        self._fmt_number = QTextCharFormat()
        self._fmt_number.setForeground(QColor("#D19A66"))

        self._fmt_event_type_key = QTextCharFormat()
        self._fmt_event_type_key.setForeground(QColor("#5C6370"))

    def _is_control_flow_name(self, name: str) -> bool:
        """ALL_CAPS names (with underscores) are treated as control-flow/special opcodes."""
        # Check if the name is all uppercase (ignoring underscores, digits, spaces)
        stripped = name.replace("_", "").replace(" ", "")
        return stripped.isupper() and len(stripped) > 1

    def highlightBlock(self, text: str):
        if not text.startswith("#"):
            return

        m = re.match(r'(#\d+)\s+', text)
        if m:
            self.setFormat(m.start(), m.end() - m.start(), self._fmt_index)
            rest_start = m.end()
        else:
            return

        colon_pos = text.find(":", rest_start)
        if colon_pos < 0:
            return

        event_name = text[rest_start:colon_pos].strip()
        # ALL_CAPS names -> purple (control flow), mixed case -> red (normal)
        fmt = self._fmt_control_flow if self._is_control_flow_name(event_name) else self._fmt_event_name
        self.setFormat(rest_start, colon_pos - rest_start, fmt)

        params_text = text[colon_pos + 1:]
        offset = colon_pos + 1

        et_m = re.search(r'(event_type)=(-?\d+)', params_text)
        if et_m:
            self.setFormat(offset + et_m.start(1), len(et_m.group(1)), self._fmt_event_type_key)
            self.setFormat(offset + et_m.start(2), len(et_m.group(2)), self._fmt_number)

        # Values can contain: letters, digits, underscore, hyphen, ?, /, +, .
        for pm in re.finditer(r',\s*(\w+)=([A-Za-z0-9_\-\?\+\/\.]+)', params_text):
            name_s, name_e = pm.start(1), pm.end(1)
            val_s, val_e = pm.start(2), pm.end(2)
            self.setFormat(offset + name_s, name_e - name_s, self._fmt_param_name)

            val = pm.group(2)
            if re.match(r'^-?\d+$', val):
                self.setFormat(offset + val_s, val_e - val_s, self._fmt_number)
            else:
                self.setFormat(offset + val_s, val_e - val_s, self._fmt_enum_value)


class GutterArea(QWidget):
    def __init__(self, editor: "ScriptTextView"):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.gutter_width(), 0)

    def paintEvent(self, event):
        self.editor.gutter_paint(event)


class ScriptTextView(QPlainTextEdit):
    line_clicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFont(QFont("Consolas, Menlo, DejaVu Sans Mono, monospace", 10))
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #282C34;
                color: #ABB2BF;
                selection-background-color: #3E4451;
                border: none;
            }
        """)

        self._highlighter = EVScriptHighlighter(self.document())
        self._gutter = GutterArea(self)
        self.blockCountChanged.connect(self._update_gutter_width)
        self.updateRequest.connect(self._update_gutter)
        self._update_gutter_width()

        self._flow_info: list[FlowInfo] = []
        self._show_warnings = True
        self.cursorPositionChanged.connect(self._on_cursor_moved)

    @property
    def show_warnings(self) -> bool:
        return self._show_warnings

    @show_warnings.setter
    def show_warnings(self, val: bool):
        self._show_warnings = val
        self._gutter.update()

    def set_flow_info(self, flow_info: list[FlowInfo]):
        self._flow_info = flow_info
        self._gutter.update()

    def gutter_width(self) -> int:
        return 32

    def _update_gutter_width(self):
        self.setViewportMargins(self.gutter_width(), 0, 0, 0)

    def _update_gutter(self, rect, dy):
        if dy:
            self._gutter.scroll(0, dy)
        else:
            self._gutter.update(0, rect.y(), self._gutter.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_gutter_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._gutter.setGeometry(
            QRect(cr.left(), cr.top(), self.gutter_width(), cr.height())
        )

    def gutter_paint(self, event):
        painter = QPainter(self._gutter)
        painter.fillRect(event.rect(), QColor("#21252B"))

        block = self.firstVisibleBlock()
        block_num = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                if block_num < len(self._flow_info):
                    fi = self._flow_info[block_num]
                    cy = top + (bottom - top) // 2

                    # Color dot
                    if fi.link_group and fi.link_group in GROUP_COLORS:
                        color = QColor(GROUP_COLORS[fi.link_group])
                        painter.setBrush(QBrush(color))
                        painter.setPen(Qt.NoPen)
                        painter.drawEllipse(4, cy - 4, 8, 8)

                    # Warning
                    if self._show_warnings and fi.warnings:
                        painter.setPen(QPen(QColor("#E5C07B")))
                        painter.setFont(QFont("", 9))
                        painter.drawText(16, cy + 5, "⚠")

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_num += 1

        painter.end()

    def _on_cursor_moved(self):
        selections = []
        sel = QTextEdit.ExtraSelection()
        sel.format.setBackground(QColor("#2C313A"))
        sel.format.setProperty(QTextFormat.FullWidthSelection, True)
        sel.cursor = self.textCursor()
        sel.cursor.clearSelection()
        selections.append(sel)

        line_idx = self.textCursor().blockNumber()
        if line_idx < len(self._flow_info):
            fi = self._flow_info[line_idx]

            for partner_idx in fi.link_partners:
                block = self.document().findBlockByNumber(partner_idx)
                if block.isValid():
                    psel = QTextEdit.ExtraSelection()
                    psel.format.setBackground(QColor("#3A3F4B"))
                    psel.format.setProperty(QTextFormat.FullWidthSelection, True)
                    psel.cursor = QTextCursor(block)
                    psel.cursor.clearSelection()
                    selections.append(psel)

            bp = fi.block_partner
            if bp is not None and bp >= 0:
                block = self.document().findBlockByNumber(bp)
                if block.isValid():
                    bsel = QTextEdit.ExtraSelection()
                    bsel.format.setBackground(QColor("#3D3145"))
                    bsel.format.setProperty(QTextFormat.FullWidthSelection, True)
                    bsel.cursor = QTextCursor(block)
                    bsel.cursor.clearSelection()
                    selections.append(bsel)

        self.setExtraSelections(selections)
        self.line_clicked.emit(line_idx)

    def highlight_entry(self, index: int):
        block = self.document().findBlockByNumber(index)
        if block.isValid():
            cursor = QTextCursor(block)
            self.setTextCursor(cursor)
            self.centerCursor()
