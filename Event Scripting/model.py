"""
FE3H Event Script Editor - Data Model
Core model that both views (text and block) observe.
"""

from dataclasses import dataclass, field
from typing import Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QUndoStack, QUndoCommand

import event_definitions as events
import event_enums as enums


@dataclass
class ScriptEntry:
    """A single event script command with its 11 parameters."""
    event_type: int = 0
    params: list = field(default_factory=lambda: [0] * 11)

    def clone(self) -> "ScriptEntry":
        return ScriptEntry(self.event_type, list(self.params))

    @property
    def name(self) -> str:
        return events.event_names.get(self.event_type, f"Unknown({self.event_type})")

    @property
    def param_count(self) -> Optional[int]:
        return events.event_param_counts.get(self.event_type)

    def get_param_info(self, param_index: int):
        """Returns (name, enum_dict_or_None) for a given 1-based param index."""
        from event_script import get_param_info
        return get_param_info(self.event_type, param_index, self.params)

    def format_param(self, param_index: int) -> str:
        """Returns the display string for a param value."""
        from event_script import format_param_value, get_param_info
        name, enum_cls = get_param_info(self.event_type, param_index, self.params)
        value = self.params[param_index - 1]
        return format_param_value(value, enum_cls, self.event_type, param_index)

    def to_text_line(self, index: int) -> str:
        """Serialize to the text format: #N EventName: event_type=X, name=val, ..."""
        from event_script import get_param_info, format_param_value

        label = events.event_names.get(self.event_type, "Unknown")
        parts = [f"event_type={self.event_type}"]

        formatted = []
        for i in range(1, 12):
            pname, penum = get_param_info(self.event_type, i, self.params)
            vstr = format_param_value(self.params[i - 1], penum, self.event_type, i)
            formatted.append((pname, vstr))

        # Trim trailing zeros
        known = events.event_param_counts.get(self.event_type)
        if known is not None:
            formatted = formatted[:known]
        else:
            while formatted and formatted[-1][1] == "0":
                formatted.pop()

        parts.extend(f"{n}={v}" for n, v in formatted)
        return f"#{index} {label}: {', '.join(parts)}"

    @staticmethod
    def from_text_line(line: str) -> Optional["ScriptEntry"]:
        """Parse a text line back into a ScriptEntry. Returns None on failure."""
        from event_script import get_param_info, get_enum_value

        if not line.startswith("#") or ":" not in line:
            return None

        try:
            _, param_part = line.split(":", 1)
            param_part = param_part.strip()
            kv_pairs = [kv.strip() for kv in param_part.split(",") if "=" in kv]
            kv_dict = dict(kv.split("=", 1) for kv in kv_pairs)

            if "event_type" not in kv_dict:
                return None

            event_type = int(kv_dict["event_type"])
            params = [0] * 11

            # First pass: resolve raw param values for context-dependent lookups
            raw_param_values = []
            for i in range(1, 12):
                base_info = events.event_param_definitions.get(event_type, {}).get(
                    i, (f"param{i}", None)
                )
                fname, _ = base_info
                raw_param_values.append(kv_dict.get(fname, "0"))

            # Second pass: resolve with context
            for i in range(1, 12):
                fname, fenum = get_param_info(event_type, i, raw_param_values)
                val = kv_dict.get(fname, "0")
                if fenum is not None:
                    params[i - 1] = get_enum_value(fenum, val, event_type, i)
                else:
                    try:
                        params[i - 1] = int(val)
                    except ValueError:
                        params[i - 1] = 0

            return ScriptEntry(event_type, params)
        except Exception:
            return None


class ScriptModel(QObject):
    """
    Central model holding the script entry list.
    Both views observe this via signals.
    """
    entries_changed = Signal()       # Full reload (file open, etc.)
    entry_modified = Signal(int)     # Single entry changed at index
    entry_inserted = Signal(int)     # Entry inserted at index
    entry_removed = Signal(int)      # Entry removed from index
    entries_moved = Signal(int, int) # Entry moved from old_idx to new_idx
    dirty_changed = Signal(bool)     # Unsaved changes flag

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries: list[ScriptEntry] = []
        self._undo_stack = QUndoStack(self)
        self._dirty = False
        self._filepath: Optional[str] = None
        self._undo_stack.cleanChanged.connect(self._on_clean_changed)

    def _on_clean_changed(self, clean: bool):
        self._dirty = not clean
        self.dirty_changed.emit(self._dirty)

    @property
    def dirty(self) -> bool:
        return self._dirty

    @property
    def filepath(self) -> Optional[str]:
        return self._filepath

    @filepath.setter
    def filepath(self, path: Optional[str]):
        self._filepath = path

    @property
    def undo_stack(self) -> QUndoStack:
        return self._undo_stack

    def count(self) -> int:
        return len(self._entries)

    def entry(self, index: int) -> ScriptEntry:
        return self._entries[index]

    def entries(self) -> list[ScriptEntry]:
        return self._entries

    def set_entries(self, entries: list[ScriptEntry]):
        """Replace all entries (file open). Clears undo stack."""
        self._entries = entries
        self._undo_stack.clear()
        self._undo_stack.setClean()
        self.entries_changed.emit()

    def set_param(self, entry_idx: int, param_idx: int, value: int):
        """Set a single parameter via undo command. param_idx is 1-based."""
        old = self._entries[entry_idx].params[param_idx - 1]
        if old == value:
            return
        cmd = SetParamCommand(self, entry_idx, param_idx, old, value)
        self._undo_stack.push(cmd)

    def set_event_type(self, entry_idx: int, new_type: int):
        old = self._entries[entry_idx].event_type
        if old == new_type:
            return
        cmd = SetEventTypeCommand(self, entry_idx, old, new_type)
        self._undo_stack.push(cmd)

    def insert_entry(self, index: int, entry: Optional[ScriptEntry] = None):
        if entry is None:
            entry = ScriptEntry()
        cmd = InsertEntryCommand(self, index, entry)
        self._undo_stack.push(cmd)

    def remove_entry(self, index: int):
        cmd = RemoveEntryCommand(self, index, self._entries[index].clone())
        self._undo_stack.push(cmd)

    def move_entry(self, from_idx: int, to_idx: int):
        if from_idx == to_idx:
            return
        cmd = MoveEntryCommand(self, from_idx, to_idx)
        self._undo_stack.push(cmd)

    def to_text(self) -> str:
        """Serialize entire model to text with auto-numbered indices."""
        return "\n".join(e.to_text_line(i) for i, e in enumerate(self._entries))

    def from_text(self, text: str):
        """Parse text into entries and replace model contents."""
        entries = []
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            entry = ScriptEntry.from_text_line(line)
            if entry is not None:
                entries.append(entry)
        self.set_entries(entries)


#
# Undo Commands
#

class SetParamCommand(QUndoCommand):
    def __init__(self, model: ScriptModel, entry_idx: int, param_idx: int,
                 old_val: int, new_val: int):
        super().__init__(f"Set param {param_idx} of #{entry_idx}")
        self.model = model
        self.entry_idx = entry_idx
        self.param_idx = param_idx
        self.old_val = old_val
        self.new_val = new_val

    def redo(self):
        self.model._entries[self.entry_idx].params[self.param_idx - 1] = self.new_val
        self.model.entry_modified.emit(self.entry_idx)

    def undo(self):
        self.model._entries[self.entry_idx].params[self.param_idx - 1] = self.old_val
        self.model.entry_modified.emit(self.entry_idx)

    def id(self):
        return 1000 + self.entry_idx * 100 + self.param_idx

    def mergeWith(self, other):
        if isinstance(other, SetParamCommand) and other.id() == self.id():
            self.new_val = other.new_val
            return True
        return False


class SetEventTypeCommand(QUndoCommand):
    def __init__(self, model: ScriptModel, entry_idx: int, old_type: int, new_type: int):
        super().__init__(f"Change type of #{entry_idx}")
        self.model = model
        self.entry_idx = entry_idx
        self.old_type = old_type
        self.new_type = new_type

    def redo(self):
        self.model._entries[self.entry_idx].event_type = self.new_type
        self.model.entry_modified.emit(self.entry_idx)

    def undo(self):
        self.model._entries[self.entry_idx].event_type = self.old_type
        self.model.entry_modified.emit(self.entry_idx)


class InsertEntryCommand(QUndoCommand):
    def __init__(self, model: ScriptModel, index: int, entry: ScriptEntry):
        super().__init__(f"Insert #{index}")
        self.model = model
        self.index = index
        self.entry = entry

    def redo(self):
        self.model._entries.insert(self.index, self.entry)
        self.model.entry_inserted.emit(self.index)

    def undo(self):
        self.model._entries.pop(self.index)
        self.model.entry_removed.emit(self.index)


class RemoveEntryCommand(QUndoCommand):
    def __init__(self, model: ScriptModel, index: int, entry: ScriptEntry):
        super().__init__(f"Remove #{index}")
        self.model = model
        self.index = index
        self.entry = entry

    def redo(self):
        self.model._entries.pop(self.index)
        self.model.entry_removed.emit(self.index)

    def undo(self):
        self.model._entries.insert(self.index, self.entry)
        self.model.entry_inserted.emit(self.index)


class MoveEntryCommand(QUndoCommand):
    def __init__(self, model: ScriptModel, from_idx: int, to_idx: int):
        super().__init__(f"Move #{from_idx} → #{to_idx}")
        self.model = model
        self.from_idx = from_idx
        self.to_idx = to_idx

    def redo(self):
        e = self.model._entries.pop(self.from_idx)
        self.model._entries.insert(self.to_idx, e)
        self.model.entries_moved.emit(self.from_idx, self.to_idx)

    def undo(self):
        e = self.model._entries.pop(self.to_idx)
        self.model._entries.insert(self.from_idx, e)
        self.model.entries_moved.emit(self.to_idx, self.from_idx)
