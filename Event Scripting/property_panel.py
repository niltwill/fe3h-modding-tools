"""
FE3H Event Script Editor - Property Panel
Shows parameter editors with searchable enum dropdowns for the selected entry.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox,
    QScrollArea, QFrame, QGroupBox, QCompleter
)
from PySide6.QtGui import QFont

import event_definitions as events
import event_enums as enums
from model import ScriptModel, ScriptEntry


class SearchableComboBox(QComboBox):
    """QComboBox with type-ahead filtering for large enum lists."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setMaxVisibleItems(20)
        self.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.completer().setFilterMode(Qt.MatchContains)


class PropertyPanel(QWidget):
    """Right-side panel showing editable parameters for the selected script entry."""

    param_changed = Signal(int, int, int)  # entry_idx, param_idx (1-based), new_value

    def __init__(self, model: ScriptModel, parent=None):
        super().__init__(parent)
        self.setObjectName("prop_panel_root")
        self.model = model
        self._current_idx = -1
        self._updating = False

        self._setup_ui()
        self.model.entry_modified.connect(self._on_entry_modified)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        self._header = QLabel("No selection")
        self._header.setFont(QFont("", 11, QFont.Bold))
        self._header.setWordWrap(True)
        layout.addWidget(self._header)

        self._idx_label = QLabel("")
        self._idx_label.setStyleSheet("color: #888;")
        layout.addWidget(self._idx_label)

        # Event type selector
        type_group = QGroupBox("Event Type")
        type_layout = QHBoxLayout(type_group)
        self._type_combo = SearchableComboBox()
        self._populate_event_type_combo()
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self._type_combo)
        layout.addWidget(type_group)

        # Scrollable parameter area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self._param_container = QWidget()
        self._param_container.setStyleSheet("background-color: #21252B;")
        self._param_layout = QVBoxLayout(self._param_container)
        self._param_layout.setContentsMargins(0, 0, 0, 0)
        self._param_layout.addStretch()
        scroll.setWidget(self._param_container)
        layout.addWidget(scroll, stretch=1)

        self._param_widgets = []

    def _populate_event_type_combo(self):
        self._type_combo.blockSignals(True)
        self._type_combo.clear()
        all_types = sorted(events.event_names.keys())
        for et in all_types:
            name = events.event_names[et]
            self._type_combo.addItem(f"{et}: {name}", et)
        self._type_combo.blockSignals(False)

    def set_selected_entry(self, index: int):
        """Called when the user clicks a line - always rebuild for fresh data."""
        self._current_idx = index
        self._rebuild_panel()

    def clear_selection(self):
        self._current_idx = -1
        self._header.setText("No selection")
        self._idx_label.setText("")
        self._type_combo.blockSignals(True)
        self._type_combo.setCurrentIndex(-1)
        self._type_combo.blockSignals(False)
        self._clear_params()

    def _on_entry_modified(self, idx: int):
        if idx == self._current_idx:
            self._rebuild_panel()

    def _rebuild_panel(self):
        if self._current_idx < 0 or self._current_idx >= self.model.count():
            self.clear_selection()
            return

        self._updating = True
        entry = self.model.entry(self._current_idx)

        self._header.setText(entry.name)
        self._idx_label.setText(f"Entry #{self._current_idx}  |  event_type={entry.event_type}")

        # Update type combo to match actual entry
        self._type_combo.blockSignals(True)
        type_idx = self._type_combo.findData(entry.event_type)
        if type_idx >= 0:
            self._type_combo.setCurrentIndex(type_idx)
        else:
            # Unknown type - add temporarily
            self._type_combo.addItem(f"{entry.event_type}: Unknown", entry.event_type)
            self._type_combo.setCurrentIndex(self._type_combo.count() - 1)
        self._type_combo.blockSignals(False)

        self._clear_params()
        self._build_param_editors(entry)
        self._updating = False

    def _clear_params(self):
        for label, widget, _ in self._param_widgets:
            label.setParent(None)
            label.deleteLater()
            widget.setParent(None)
            widget.deleteLater()
        self._param_widgets = []

    def _build_param_editors(self, entry: ScriptEntry):
        from event_script import get_param_info

        known_count = entry.param_count
        if known_count is None:
            known_count = 11

        insert_before = self._param_layout.count() - 1  # Before the stretch

        for pi in range(1, known_count + 1):
            pname, penum = get_param_info(entry.event_type, pi, entry.params)
            value = entry.params[pi - 1]
            override_map = enums.enum_overrides.get(entry.event_type, {}).get(pi, {})

            label = QLabel(f"{pname}:")
            label.setStyleSheet("font-weight: bold; margin-top: 4px; color: #ABB2BF;")
            self._param_layout.insertWidget(insert_before, label)
            insert_before += 1

            if penum is not None and isinstance(penum, dict):
                widget = self._make_enum_combo(penum, override_map, value, pi)
            else:
                widget = self._make_int_spinbox(value, pi)

            self._param_layout.insertWidget(insert_before, widget)
            insert_before += 1
            self._param_widgets.append((label, widget, pi))

    def _make_enum_combo(self, enum_dict: dict, override_map: dict,
                         current_value: int, param_idx: int) -> SearchableComboBox:
        combo = SearchableComboBox()
        combo.setProperty("param_idx", param_idx)

        merged = dict(enum_dict)
        merged.update(override_map)
        sorted_items = sorted(merged.items(), key=lambda x: (x[0] >= 0, x[0]))

        current_combo_idx = -1
        for i, (key, label) in enumerate(sorted_items):
            display = f"{label}  ({key})"
            combo.addItem(display, key)
            if key == current_value:
                current_combo_idx = i

        if current_combo_idx < 0:
            combo.addItem(f"[raw] {current_value}", current_value)
            current_combo_idx = combo.count() - 1

        combo.setCurrentIndex(current_combo_idx)
        combo.currentIndexChanged.connect(
            lambda idx, c=combo, pi=param_idx: self._on_combo_changed(c, pi)
        )
        return combo

    def _make_int_spinbox(self, current_value: int, param_idx: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(-2147483648, 2147483647)
        spin.setValue(current_value)
        spin.setProperty("param_idx", param_idx)
        spin.valueChanged.connect(
            lambda val, pi=param_idx: self._on_spin_changed(val, pi)
        )
        return spin

    def _on_combo_changed(self, combo: QComboBox, param_idx: int):
        if self._updating or self._current_idx < 0:
            return
        value = combo.currentData()
        if value is not None:
            self.param_changed.emit(self._current_idx, param_idx, value)

    def _on_spin_changed(self, value: int, param_idx: int):
        if self._updating or self._current_idx < 0:
            return
        self.param_changed.emit(self._current_idx, param_idx, value)

    def _on_type_changed(self, combo_idx: int):
        if self._updating or self._current_idx < 0:
            return
        new_type = self._type_combo.currentData()
        if new_type is not None:
            self.model.set_event_type(self._current_idx, new_type)
