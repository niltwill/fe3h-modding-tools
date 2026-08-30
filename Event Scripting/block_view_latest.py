"""
FE3H Event Script Editor - Block View
QGraphicsScene-based visual rendering with color-coded blocks,
nesting brackets, and inline param editors on double-click.
"""

from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsPathItem, QGraphicsItem,
    QGraphicsProxyWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QSpinBox, QCompleter
)
from PySide6.QtGui import (
    QColor, QPen, QBrush, QFont, QPainterPath,
    QPainter, QFontMetrics
)

from model import ScriptModel
from control_flow import (
    analyze_control_flow, FlowInfo, GROUP_COLORS,
    CONDITIONAL_OPENERS, CONDITIONAL_ELSE, CONDITIONAL_END,
    SUB_CALL, SUB_RETURN, QUEUE_BEGIN, QUEUE_COMMIT
)
import event_definitions as events
import event_enums as enums

#
# Category Classification
#

CATEGORY_COLORS = {
    "scene_setup":  "#5C6370",
    "dialogue":     "#61AFEF",
    "animation":    "#E5C07B",
    "camera":       "#56B6C2",
    "audio":        "#98C379",
    "voice_arm":    "#E06C75",
    "control":      "#C678DD",
    "conditional":  "#C678DD",
    "subroutine":   "#7F848E",  # Grey - distinct from conditional purple
    "support":      "#D19A66",
    "queue":        "#56B6C2",  # Cyan - distinct from conditional purple
    "unknown":      "#5C6370",
}

CATEGORY_MAP = {}

def _register(category, type_ids):
    for t in type_ids:
        CATEGORY_MAP[t] = category

_register("scene_setup", [0, 1, 28, 29, 25, 83, 136, 10, 4, 5, 43, 93])
_register("dialogue", [3, 81, 90, 113, 85, 9])
_register("animation", [11, 23, 24, 69, 98, 96, 67, 94, 91, 104, 103, 102, 107, 108, 86, 132, 134, 142, 143])
_register("camera", [87, 73, 54, 100, 101, 140, 122, 31])
_register("audio", [15, 16, 52, 114, 133, 17, 66, 27, 38, 59, 30, 20])
_register("voice_arm", [89, 33, 34, 123, 118, 130])
_register("control", [13, 97, 8, 14, 39, 119, 120, 144, 155, 156])
_register("conditional", [35, 36, 37, 79, 80, 82, 124, 125, 126, 127, 128])
_register("subroutine", [40, 41, 42])
_register("support", [45, 46, 95, 147, 148, 99])
_register("queue", [135, 138])

def get_category(event_type):
    return CATEGORY_MAP.get(event_type, "unknown")

def get_category_color(event_type):
    return CATEGORY_COLORS.get(get_category(event_type), "#5C6370")


#
# Condensed Summary
#

def summarize_entry(entry):
    from event_script import get_param_info, format_param_value
    et = entry.event_type
    params = entry.params

    if et == 3 or et == 81:
        _, ce = get_param_info(et, 1, params)
        cv = format_param_value(params[0], ce, et, 1)
        _, ae = get_param_info(et, 3, params)
        av = format_param_value(params[2], ae, et, 2)
        _, pe = get_param_info(et, 4, params)
        pv = format_param_value(params[3], pe, et, 3)
        return f"{cv}: text_line={params[1]}, voice_line={params[4]}, portrait={pv}, anim={av}"
    if et == 11:
        _, ce = get_param_info(et, 1, params)
        cv = format_param_value(params[0], ce, et, 1)
        _, ae = get_param_info(et, 2, params)
        av = format_param_value(params[1], ae, et, 2)
        if params[4] > 0:
            return f"{cv}: {av}, {params[4]} frames"
        else:
            return f"{cv}: {av}"
    if et == 0:
        _, e = get_param_info(et, 1, params)
        return format_param_value(params[0], e, et, 1)
    if et == 15:
        _, e = get_param_info(et, 1, params)
        value = format_param_value(params[0], e, et, 1)
        if params[0] != -1:
            return f"{value}"
        else:
            return f"(silence)"
    if et == 17:
        _, e = get_param_info(et, 1, params)
        value = format_param_value(params[0], e, et, 1)
        return f"{value}"
    if et == 13:
        return f"{params[0]} frames"
    if et == 83:
        _, oe = get_param_info(et, 1, params)
        ov = format_param_value(params[0], oe, et, 1)
        _, se = get_param_info(et, 2, params)
        sv = format_param_value(params[1], se, et, 2)
        return f"{ov} {sv}"
    if et == 85:
        _, ce = get_param_info(et, 1, params)
        cv = format_param_value(params[0], ce, et, 1)
        _, oe = get_param_info(et, 2, params)
        ov = format_param_value(params[1], oe, et, 2)
        _, ne = get_param_info(et, 3, params)
        nv = format_param_value(params[2], ne, et, 3)
        _, pe = get_param_info(et, 4, params)
        pv = format_param_value(params[3], pe, et, 4)
        if params[2] == 1:
            return f"{cv}: enable_changes={nv}, name_override={ov}, hide_portrait={pv}"
        else:
            return f"{cv}: enable_changes={nv}"
    if et in (1, 4, 5, 28, 79, 139):
        mandatory_params = {
            1: [],
            4: [1],
            5: [1],
            28: [],
            79: [1, 2],
            139: [1]
        }.get(et, [])

        pieces = []
        # Always show mandatory params first
        for pi in mandatory_params:
            pn, pe = get_param_info(et, pi, params)
            pv = format_param_value(params[pi - 1], pe, et, pi)
            pieces.append(f"{pn}={pv}" if pn else pv)

        # Show remaining params up to 11 if they are not -1
        for pi in range(1, 12):
            if pi in mandatory_params:
                continue
            if params[pi - 1] != -1:
                pn, pe = get_param_info(et, pi, params)
                pv = format_param_value(params[pi - 1], pe, et, pi)
                pieces.append(f"{pn}={pv}" if pn else pv)

        return ", ".join(pieces) if pieces else ""
    if et == 73:
        _, ce = get_param_info(et, 1, params)
        cv = format_param_value(params[0], ce, et, 1)
        _, ch = get_param_info(et, 2, params)
        chv = format_param_value(params[1], ch, et, 2)
        return f"{cv} → {chv}"
    if et == 87:
        _, ce = get_param_info(et, 2, params)
        cv = format_param_value(params[1], ce, et, 1)
        return f"panning={cv}, angle={params[0]}"
    if et in (24, 69, 23):
        _, ce = get_param_info(et, 1, params)
        cv = format_param_value(params[0], ce, et, 1)
        _, de = get_param_info(et, 2, params)
        dv = format_param_value(params[1], de, et, 2)
        return f"{cv}: {dv}, {params[2]} frames"
    if et == 98:
        _, ce = get_param_info(et, 1, params)
        cv = format_param_value(params[0], ce, et, 1)
        _, ee = get_param_info(et, 2, params)
        ev = format_param_value(params[1], ee, et, 2)
        return f"{cv}: {ev}, {params[2]} frames"
    if et == 96:
        _, ce = get_param_info(et, 1, params)
        cv = format_param_value(params[0], ce, et, 1)
        _, ee = get_param_info(et, 2, params)
        ev = format_param_value(params[1], ee, et, 2)
        return f"{cv}: {ev}"
    if et == 128:
        _, ce = get_param_info(et, 1, params)
        cv = format_param_value(params[0], ce, et, 1)
        _, ee = get_param_info(et, 2, params)
        ev = format_param_value(params[1], ee, et, 2)
        return f"flag={cv}, expected_value={ev}"
    if et == 135:
        return f"{params[0]} frames"
    if et == 35:
        _, ce = get_param_info(et, 1, params)
        cv = format_param_value(params[0], ce, et, 1)
        return f"{cv}, expected={params[1]}"
    if et in (33, 34):
        slots = params[1:3] if et == 33 else params[1:4]
        return f"var={params[0]}, text_ids={slots}"
    if et == 89:
        return f"var={params[0]}, text_id={params[1]}"
    if et == 43:
        _, ce = get_param_info(et, 1, params)
        cv = format_param_value(params[0], ce, et, 1)
        _, ve = get_param_info(et, 2, params)
        vv = format_param_value(params[1], ve, et, 2)
        return f"{cv}: {vv}"
    if et == 45:
        _, ce = get_param_info(et, 1, params)
        cv = format_param_value(params[0], ce, et, 1)
        _, de = get_param_info(et, 2, params)
        dv = format_param_value(params[1], de, et, 2)
        return f"{cv}: {dv}"

    pc = entry.param_count or 3
    pieces = []
    for i in range(1, min(pc + 1, 4)):
        if params[i - 1] != 0:
            pn, pe = get_param_info(et, i, params)
            pv = format_param_value(params[i - 1], pe, et, i)
            pieces.append(f"{pn}={pv}")
    return ", ".join(pieces) if pieces else ""


def conditional_collapse_summary(opener_idx, entries, flow_infos):
    """Generate a rich summary for a collapsed conditional block."""
    from event_script import get_param_info, format_param_value

    entry = entries[opener_idx]
    fi = flow_infos[opener_idx]
    et = entry.event_type
    params = entry.params
    partner = fi.block_partner

    inner_count = (partner - opener_idx - 1) if (partner is not None and partner >= 0) else 0

    # Check for ELSE branch
    has_else = False
    if partner is not None and partner >= 0:
        for j in range(opener_idx + 1, partner):
            if j < len(flow_infos) and flow_infos[j].is_else:
                has_else = True
                break

    # Check for nested conditionals
    nested_count = 0
    if partner is not None and partner >= 0:
        for j in range(opener_idx + 1, partner):
            if j < len(flow_infos) and flow_infos[j].is_opener:
                nested_count += 1

    # Build condition description
    if et == 35:  # CONDITIONAL STATEMENT
        cond_type = params[0]
        expected = params[1]
        if cond_type == 0:
            desc = f"var[{params[2]}] == {expected}"
        elif cond_type == 1:
            _, ge = get_param_info(et, 2, params)
            gv = format_param_value(expected, ge, et, 2)
            desc = f"gender is {gv}"
        elif cond_type == 2:
            desc = f"has item (flag {params[2]})"
        elif cond_type == 4:
            _, re = get_param_info(et, 2, params)
            rv = format_param_value(expected, re, et, 2)
            desc = f"route is {rv}"
        elif cond_type == 5 or cond_type == 6:
            _, fe = get_param_info(et, 3, params)
            fv = format_param_value(params[2], fe, et, 3)
            desc = f"flag {fv} == {expected}"
        elif cond_type == 7 or cond_type == 8:
            _, ce = get_param_info(et, 3, params)
            cv = format_param_value(params[2], ce, et, 3)
            _, re2 = get_param_info(et, 2, params)
            rv2 = format_param_value(expected, re2, et, 2)
            desc = f"support({cv}) >= {rv2}"
        else:
            _, ct_enum = get_param_info(et, 1, params)
            ct_label = format_param_value(cond_type, ct_enum, et, 1)
            desc = f"{ct_label} == {expected}"
    elif et == 79:
        _, ce = get_param_info(et, 1, params)
        cv = format_param_value(params[0], ce, et, 1)
        desc = f"character is {cv}"
    elif et == 80:
        desc = "support level"
    elif et == 82:
        desc = "party size"
    elif et in (124, 125, 126, 127, 128):
        desc = entry.name.replace("CONDITIONAL_", "").lower().replace("_", " ")
    elif et == SUB_CALL:
        desc = "subroutine"
    else:
        desc = "condition"

    parts = [f"IF {desc}"]
    if has_else:
        parts.append("+ ELSE")
    if nested_count > 0:
        parts.append(f"({nested_count} nested)")
    parts.append(f"[{inner_count} cmds]")

    return "  ".join(parts)


#
# Inline Editor Widget
#

EDITOR_STYLESHEET = """
    QWidget#block_editor { background: transparent; }
    QLabel { color: #61AFEF; font-size: 8pt; }
    QComboBox {
        background-color: #282C34; color: #ABB2BF;
        border: 1px solid #3E4451; border-radius: 2px;
        padding: 2px 4px; font-size: 8pt; max-height: 20px;
    }
    QComboBox QAbstractItemView {
        background-color: #282C34; color: #ABB2BF;
        selection-background-color: #3E4451;
    }
    QComboBox QLineEdit {
        background-color: #282C34; color: #ABB2BF;
        border: none; padding: 0;
    }
    QSpinBox {
        background-color: #282C34; color: #ABB2BF;
        border: 1px solid #3E4451; border-radius: 2px;
        padding: 2px 4px; font-size: 8pt; max-height: 20px;
    }
"""

PARAM_ROW_HEIGHT = 26


def create_editor_widget(entry, model, entry_index, on_change_callback):
    """Create a QWidget with param editors for embedding in a block."""
    from event_script import get_param_info

    container = QWidget()
    container.setObjectName("block_editor")
    container.setStyleSheet(EDITOR_STYLESHEET)
    layout = QVBoxLayout(container)
    layout.setContentsMargins(4, 2, 4, 4)
    layout.setSpacing(2)

    known_count = entry.param_count
    if known_count is None:
        known_count = 11

    for pi in range(1, known_count + 1):
        pname, penum = get_param_info(entry.event_type, pi, entry.params)
        value = entry.params[pi - 1]
        override_map = enums.enum_overrides.get(entry.event_type, {}).get(pi, {})

        row = QHBoxLayout()
        row.setSpacing(4)

        label = QLabel(f"{pname}:")
        label.setFixedWidth(120)
        row.addWidget(label)

        if penum is not None and isinstance(penum, dict):
            combo = QComboBox()
            combo.setEditable(True)
            combo.setInsertPolicy(QComboBox.NoInsert)
            combo.setMaxVisibleItems(15)
            combo.completer().setCompletionMode(QCompleter.PopupCompletion)
            combo.completer().setFilterMode(Qt.MatchContains)

            merged = dict(penum)
            merged.update(override_map)
            sorted_items = sorted(merged.items(), key=lambda x: (x[0] >= 0, x[0]))

            current_idx = -1
            for idx, (key, lbl) in enumerate(sorted_items):
                combo.addItem(f"{lbl}  ({key})", key)
                if key == value:
                    current_idx = idx

            if current_idx < 0:
                combo.addItem(f"[raw] {value}", value)
                current_idx = combo.count() - 1

            combo.setCurrentIndex(current_idx)

            _pi = pi  # capture
            combo.currentIndexChanged.connect(
                lambda idx, c=combo, p=_pi: on_change_callback(entry_index, p, c.currentData())
            )
            row.addWidget(combo, stretch=1)
        else:
            spin = QSpinBox()
            spin.setRange(-2147483648, 2147483647)
            spin.setValue(value)

            _pi = pi
            spin.valueChanged.connect(
                lambda val, p=_pi: on_change_callback(entry_index, p, val)
            )
            row.addWidget(spin, stretch=1)

        layout.addLayout(row)

    total_h = known_count * PARAM_ROW_HEIGHT + 8
    container.setFixedHeight(total_h)
    return container, total_h


#
# Block Constants
#

BLOCK_WIDTH = 580
BLOCK_HEADER_HEIGHT = 22
BLOCK_BODY_HEIGHT = 18
BLOCK_PADDING = 4
BLOCK_STRIPE_W = 8
INDENT_PX = 28


#
# Block Graphics Item
#

class BlockItem(QGraphicsRectItem):
    """A single script entry rendered as a colored block."""

    def __init__(self, index, entry, flow_info, parent=None):
        super().__init__(parent)
        self.entry_index = index
        self.entry = entry
        self.flow_info = flow_info

        cat = get_category(entry.event_type)
        self._cat_color = QColor(get_category_color(entry.event_type))

        self._summary = summarize_entry(entry)
        self._summary_font = QFont("Segoe UI, Arial", 8)
        self._header_font = QFont("Segoe UI, Arial", 9, QFont.Bold)
        self._summary_lines = []

        indent = flow_info.indent * INDENT_PX
        self._width = BLOCK_WIDTH - indent
        
        # Initialize all state variables before calculating height
        self._expanded = False
        self._editor_proxy = None
        self._block_collapsed = False
        self._collapse_summary = ""
        self._is_collapsible = flow_info.is_opener and entry.event_type in (
            *CONDITIONAL_OPENERS, SUB_CALL
        )
        
        # Calculate initial height
        self._collapsed_height = self._calculate_height()
        self._height = self._collapsed_height
        
        self.setRect(0, 0, self._width, self._height)

        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setAcceptHoverEvents(True)
        tip = f"#{index} {entry.name}\nDouble-click to edit"
        if self._is_collapsible:
            tip += "\nClick ▸/▾ to collapse/expand block"
        self.setToolTip(tip)

    def _wrap_text(self, text, max_width, font):
        """Wrap text to fit within max_width, returning list of lines."""
        if not text:
            return []
        
        fm = QFontMetrics(font)
        if fm.horizontalAdvance(text) <= max_width:
            return [text]
        
        lines = []
        words = text.split(' ')
        current_line = []
        current_width = 0
        
        for word in words:
            word_width = fm.horizontalAdvance(word + ' ')
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_width = fm.horizontalAdvance(word + ' ')
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines

    def _calculate_height(self):
        """Calculate the required height based on content."""
        # Base height from header
        h = BLOCK_HEADER_HEIGHT + BLOCK_PADDING * 2
        
        # Add space for summary if needed and not collapsed/expanded
        if not self._expanded and not self._block_collapsed and self._summary:
            # Calculate available width for summary text
            available_width = self._width - BLOCK_STRIPE_W - 40  # Account for padding
            
            # Wrap the summary text
            self._summary_lines = self._wrap_text(
                self._summary, 
                available_width,
                self._summary_font
            )
            
            # Add height for each line of summary
            line_height = QFontMetrics(self._summary_font).height()
            h += len(self._summary_lines) * line_height + 4  # Small padding
        
        elif self._block_collapsed and self._collapse_summary:
            # Handle collapse summary similarly
            available_width = self._width - BLOCK_STRIPE_W - 40
            self._summary_lines = self._wrap_text(
                self._collapse_summary,
                available_width,
                self._summary_font
            )
            line_height = QFontMetrics(self._summary_font).height()
            h += len(self._summary_lines) * line_height + 4
        
        return max(h, BLOCK_HEADER_HEIGHT + BLOCK_PADDING * 2)  # Ensure minimum height

    def is_expanded(self):
        return self._expanded

    def expand(self, model, on_change_callback):
        """Show inline param editors."""
        if self._expanded:
            return
        self._expanded = True

        editor_widget, editor_h = create_editor_widget(
            self.entry, model, self.entry_index, on_change_callback
        )
        editor_widget.setFixedWidth(int(self._width) - BLOCK_STRIPE_W - 12)

        self._editor_proxy = QGraphicsProxyWidget(self)
        self._editor_proxy.setWidget(editor_widget)
        self._editor_proxy.setPos(BLOCK_STRIPE_W + 6, self._collapsed_height)

        new_h = self._collapsed_height + editor_h + 4
        self._height = new_h
        self.setRect(0, 0, self._width, new_h)

        # Raise above other blocks so dropdowns aren't clipped
        self.setZValue(100)
        self.update()

    def collapse(self):
        """Hide inline param editors."""
        if not self._expanded:
            return
        self._expanded = False

        if self._editor_proxy:
            w = self._editor_proxy.widget()
            self._editor_proxy.setWidget(None)
            if w:
                w.deleteLater()
            self.scene().removeItem(self._editor_proxy)
            self._editor_proxy = None

        self._height = self._collapsed_height
        self.setRect(0, 0, self._width, self._collapsed_height)
        self.setZValue(0)
        self.update()

    def refresh_summary(self):
        """Update the summary text from current entry data (after a param change)."""
        self._summary = summarize_entry(self.entry)
        self.setToolTip(f"#{self.entry_index} {self.entry.name}\nDouble-click to edit")
        
        # Recalculate height
        new_height = self._calculate_height()
        if new_height != self._height:
            self._height = new_height
            self._collapsed_height = new_height
            self.setRect(0, 0, self._width, new_height)
        
        self.update()

    def paint(self, painter, option, widget=None):
        r = self.rect()
        is_selected = self.isSelected()

        bg = QColor("#2C313A") if not is_selected else QColor("#3E4451")
        if self._expanded:
            bg = QColor("#333842")
        if self._block_collapsed:
            bg = QColor("#2A2E36")
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg))
        painter.drawRoundedRect(r, 4, 4)

        stripe = QRectF(r.x(), r.y(), BLOCK_STRIPE_W, r.height())
        painter.setBrush(QBrush(self._cat_color))
        painter.drawRoundedRect(stripe, 3, 3)
        painter.drawRect(QRectF(r.x() + 3, r.y(), BLOCK_STRIPE_W - 3, r.height()))

        if is_selected or self._expanded or self._block_collapsed:
            pen_color = self._cat_color
            if self._expanded:
                pen_color = self._cat_color.lighter(140)
            elif self._block_collapsed:
                pen_color = self._cat_color.darker(130)
            painter.setPen(QPen(pen_color, 1.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(r.adjusted(0.5, 0.5, -0.5, -0.5), 4, 4)

        header_font = self._header_font
        painter.setFont(header_font)
        text_x = r.x() + BLOCK_STRIPE_W + 8

        # Collapse indicator for collapsible blocks
        if self._is_collapsible:
            indicator = "▾" if not self._block_collapsed else "▸"
            painter.setPen(QPen(QColor("#848B98")))
            painter.drawText(text_x, r.y() + BLOCK_PADDING + 13, indicator)
            text_x += 14  # Shift text right to make room

        text_y = r.y() + BLOCK_PADDING + 13

        # Entry number
        idx_str = f"#{self.entry_index}"
        painter.setPen(QPen(QColor("#636D83")))
        painter.drawText(text_x, text_y, idx_str)

        # Event name
        name_x = text_x + painter.fontMetrics().horizontalAdvance(idx_str) + 8
        painter.setPen(QPen(self._cat_color.lighter(130)))
        painter.drawText(name_x, text_y, self.entry.name)

        # Draw summary text (wrapped)
        if self._block_collapsed and self._collapse_summary:
            painter.setFont(self._summary_font)
            painter.setPen(QPen(QColor("#98C379")))
            
            # Draw each line of the wrapped summary
            y_offset = text_y + BLOCK_BODY_HEIGHT
            line_height = QFontMetrics(self._summary_font).height()
            for i, line in enumerate(self._summary_lines):
                painter.drawText(text_x + 4, y_offset + (i * line_height), line)
                
        elif not self._expanded and self._summary:
            painter.setFont(self._summary_font)
            painter.setPen(QPen(QColor("#848B98")))
            
            # Draw each line of the wrapped summary
            y_offset = text_y + BLOCK_BODY_HEIGHT
            line_height = QFontMetrics(self._summary_font).height()
            for i, line in enumerate(self._summary_lines):
                painter.drawText(text_x + 4, y_offset + (i * line_height), line)

    def height(self):
        return self._height


# Nesting Bracket Item

class NestingBracket(QGraphicsPathItem):
    def __init__(self, x, y_start, y_end, color, dashed=False, parent=None):
        super().__init__(parent)
        path = QPainterPath()
        path.moveTo(x, y_start)
        path.lineTo(x, y_end)
        path.moveTo(x, y_start)
        path.lineTo(x + 10, y_start)
        path.moveTo(x, y_end)
        path.lineTo(x + 10, y_end)
        self.setPath(path)
        pen = QPen(color, 1.5)
        if dashed:
            pen.setStyle(Qt.DashLine)
        self.setPen(pen)


class ConnectorLine(QGraphicsPathItem):
    """A curved line connecting two linked blocks in the right gutter."""

    def __init__(self, y_from, y_to, color, x_base, dimmed=True, parent=None):
        super().__init__(parent)
        self.source_y = y_from
        self.target_y = y_to

        # Bezier curve arcing to the right of the blocks
        path = QPainterPath()
        arc_x = x_base + 12  # How far right the arc extends

        path.moveTo(x_base, y_from)
        path.cubicTo(
            arc_x, y_from,       # Control point 1
            arc_x, y_to,         # Control point 2
            x_base, y_to         # End point
        )

        # Small dots at endpoints
        dot_r = 2.5
        path.addEllipse(x_base - dot_r, y_from - dot_r, dot_r * 2, dot_r * 2)
        path.addEllipse(x_base - dot_r, y_to - dot_r, dot_r * 2, dot_r * 2)

        self.setPath(path)

        c = QColor(color)
        if dimmed:
            c.setAlpha(60)
            pen = QPen(c, 1.0)
        else:
            c.setAlpha(200)
            pen = QPen(c, 2.0)

        self.setPen(pen)
        self.setBrush(QBrush(c) if not dimmed else Qt.NoBrush)


#
# Block Scene
#

class BlockScene(QGraphicsScene):
    entry_clicked = Signal(int)
    param_changed = Signal(int, int, int)  # entry_idx, param_idx, value
    entry_moved = Signal(int, int)         # from_idx, to_idx

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.setBackgroundBrush(QBrush(QColor("#21252B")))
        self._block_items: list[BlockItem] = []
        self._expanded_index = -1
        self._collapsed_openers: set[int] = set()  # Indices of collapsed conditional openers
        self.show_connectors = True                # Makes this feature optional, not mandatory

    def rebuild(self):
        # Preserve collapse state across rebuilds (by entry index - may shift but usually fine)
        saved_collapsed = set(self._collapsed_openers)

        self.clear()
        self._block_items = []
        self._expanded_index = -1
        self._collapsed_openers = set()

        entries = self.model.entries()
        if not entries:
            return

        flow_info = analyze_control_flow(entries)
        self._flow_info = flow_info

        for i, entry in enumerate(entries):
            fi = flow_info[i]
            block = BlockItem(i, entry, fi)
            self.addItem(block)
            self._block_items.append(block)

        # Restore collapse state
        for idx in saved_collapsed:
            if idx < len(self._block_items) and self._block_items[idx]._is_collapsible:
                self._apply_block_collapse(idx)

        self._relayout(entries, flow_info)

    def _relayout(self, entries=None, flow_info=None):
        """Position all blocks and draw brackets. Skips hidden (collapsed) blocks."""
        if entries is None:
            entries = self.model.entries()
        if flow_info is None:
            flow_info = self._flow_info if hasattr(self, '_flow_info') else analyze_control_flow(entries)

        # Build set of hidden indices (blocks inside collapsed openers)
        hidden = self._compute_hidden_set()

        # Remove bracket, divider, and connector items (keep block items)
        for item in list(self.items()):
            if isinstance(item, (NestingBracket, ConnectorLine)):
                self.removeItem(item)
            elif isinstance(item, QGraphicsPathItem) and not isinstance(item, BlockItem):
                self.removeItem(item)

        y = 10
        gap = 3
        positions = {}  # index -> (y_start, y_end)

        for i, block in enumerate(self._block_items):
            if i in hidden:
                block.setVisible(False)
                continue

            block.setVisible(True)
            fi = flow_info[i] if i < len(flow_info) else FlowInfo()
            indent = fi.indent * INDENT_PX
            x = 10 + indent
            block.setPos(x, y)
            positions[i] = (y, y + block.height())
            y += block.height() + gap

        self._draw_brackets(entries, flow_info, positions)
        # Find selected block for connector highlighting
        sel_idx = -1
        for block in self._block_items:
            if block.isSelected():
                sel_idx = block.entry_index
                break
        self._draw_connectors(flow_info, positions, sel_idx)
        self.setSceneRect(0, 0, BLOCK_WIDTH + 40, y + 20)

    def _draw_brackets(self, entries, flow_info, positions):
        for i, fi in enumerate(flow_info):
            if not fi.is_opener or i not in positions:
                continue
            if i in self._collapsed_openers:
                continue
            partner = fi.block_partner
            if partner is None or partner < 0 or partner >= len(entries):
                continue
            if partner not in positions:
                continue
            et = entries[i].event_type
            indent = fi.indent * INDENT_PX
            bx = 10 + indent + 2
            y_start = positions[i][0] + 4
            y_end = positions[partner][1] - 4

            # Use category color for brackets
            bracket_color = QColor(get_category_color(et)).darker(120)
            is_dashed = (et == QUEUE_BEGIN)
            self.addItem(NestingBracket(bx, y_start, y_end, bracket_color, dashed=is_dashed))

        for i, fi in enumerate(flow_info):
            if fi.is_else and fi.block_partner is not None and fi.block_partner >= 0:
                if i not in positions:
                    continue
                indent = fi.indent * INDENT_PX
                # Position the divider near the bottom of the ELSE block
                #y_mid = (positions[i][0] + positions[i][1]) / 2
                y_bottom = positions[i][1] - 8  # 8px from the bottom
                bx = 10 + indent + 2
                path = QPainterPath()
                path.moveTo(bx, y_bottom)
                path.lineTo(bx + BLOCK_WIDTH - indent - 20, y_bottom)
                divider = QGraphicsPathItem()
                divider.setPath(path)
                divider.setPen(QPen(QColor(get_category_color(CONDITIONAL_ELSE)).darker(150), 1, Qt.DashDotLine))
                self.addItem(divider)

    def _draw_connectors(self, flow_info, positions, selected_idx=-1):
        """Draw curved connector lines between linked opcodes."""
        if not self.show_connectors:
            return

        drawn_pairs = set()

        for i, fi in enumerate(flow_info):
            if i not in positions or not fi.link_partners:
                continue

            for partner_idx in fi.link_partners:
                if partner_idx not in positions:
                    continue

                pair_key = (min(i, partner_idx), max(i, partner_idx))
                if pair_key in drawn_pairs:
                    continue
                drawn_pairs.add(pair_key)

                group = fi.link_group
                color = GROUP_COLORS.get(group, "#5C6370") if group else "#5C6370"

                y_from = (positions[i][0] + positions[i][1]) / 2
                y_to = (positions[partner_idx][0] + positions[partner_idx][1]) / 2
                x_base = BLOCK_WIDTH + 14

                is_highlighted = (selected_idx == i or selected_idx == partner_idx)

                conn = ConnectorLine(y_from, y_to, color, x_base, dimmed=not is_highlighted)
                conn.setZValue(-1)
                self.addItem(conn)

    def update_connector_highlights(self, selected_idx: int):
        """Redraw connectors with updated highlighting for the selected block."""
        if not hasattr(self, '_flow_info'):
            return

        # Deselect all blocks if nothing selected
        if selected_idx < 0:
            for block in self._block_items:
                block.setSelected(False)

        positions = {}
        for i, block in enumerate(self._block_items):
            if block.isVisible():
                positions[i] = (block.pos().y(), block.pos().y() + block.height())

        for item in list(self.items()):
            if isinstance(item, ConnectorLine):
                self.removeItem(item)

        self._draw_connectors(self._flow_info, positions, selected_idx)

    def toggle_expand(self, index):
        """Expand a block's inline editors (collapsing any previously expanded one)."""
        if self._expanded_index >= 0 and self._expanded_index < len(self._block_items):
            self._block_items[self._expanded_index].collapse()

        if index == self._expanded_index:
            self._expanded_index = -1
        else:
            if 0 <= index < len(self._block_items):
                self._block_items[index].expand(
                    self.model, self._on_param_changed
                )
                self._expanded_index = index

        self._relayout()

    #
    # Block collapse (conditional/sub) 
    #

    def _compute_hidden_set(self) -> set:
        """Compute the set of block indices hidden by collapsed openers."""
        hidden = set()
        for opener_idx in self._collapsed_openers:
            if opener_idx >= len(self._block_items):
                continue
            fi = self._flow_info[opener_idx] if opener_idx < len(self._flow_info) else None
            if fi is None:
                continue
            partner = fi.block_partner
            if partner is None or partner < 0:
                continue
            # Hide everything from opener+1 to partner (inclusive - hides the END too)
            for j in range(opener_idx + 1, min(partner + 1, len(self._block_items))):
                hidden.add(j)
        return hidden

    def _apply_block_collapse(self, opener_idx: int):
        """Mark a block as collapsed and generate its summary."""
        if opener_idx >= len(self._block_items):
            return
        block = self._block_items[opener_idx]
        entries = self.model.entries()
        block._block_collapsed = True
        block._collapse_summary = conditional_collapse_summary(
            opener_idx, entries, self._flow_info
        )
        # Recalculate height with collapse summary
        new_height = block._calculate_height()
        block._height = new_height
        block._collapsed_height = new_height
        block.setRect(0, 0, block._width, new_height)
        self._collapsed_openers.add(opener_idx)

    def toggle_block_collapse(self, opener_idx: int):
        """Toggle collapse/expand of a conditional or subroutine block."""
        if opener_idx in self._collapsed_openers:
            # Expand
            self._collapsed_openers.discard(opener_idx)
            if opener_idx < len(self._block_items):
                block = self._block_items[opener_idx]
                block._block_collapsed = False
                block._collapse_summary = ""
                # Restore original compact height
                block._height = block._collapsed_height
                block.setRect(0, 0, block._width, block._collapsed_height)
        else:
            # Collapse - also close any expanded inline editor inside
            if self._expanded_index >= 0:
                fi = self._flow_info[opener_idx] if opener_idx < len(self._flow_info) else None
                partner = fi.block_partner if fi else -1
                if partner and opener_idx < self._expanded_index <= partner:
                    self._block_items[self._expanded_index].collapse()
                    self._expanded_index = -1

            self._apply_block_collapse(opener_idx)

        self._relayout()

    def _on_param_changed(self, entry_idx, param_idx, value):
        if value is not None:
            self.param_changed.emit(entry_idx, param_idx, value)

    def refresh_block(self, index):
        """Update a single block's summary after a param change. No rebuild needed."""
        if 0 <= index < len(self._block_items):
            self._block_items[index].refresh_summary()

    #
    # Drag-to-reorder state 
    #

    _drag_active = False
    _drag_block = None       # BlockItem being dragged
    _drag_start_y = 0.0      # Scene Y where drag started
    _drag_origin_index = -1  # Original index of the dragged block
    _drag_block_origin_pos = None  # Original scene position
    _drop_indicator = None   # Horizontal line showing insertion point
    _drop_target_index = -1  # Where the block would land

    DRAG_THRESHOLD = 8       # Pixels before drag activates

    def _find_block_at(self, scene_pos):
        """Find the BlockItem at a scene position (handles proxy children)."""
        if not self.views():
            return None
        item = self.itemAt(scene_pos, self.views()[0].transform())
        if isinstance(item, BlockItem):
            return item
        if isinstance(item, QGraphicsProxyWidget):
            parent = item.parentItem()
            if isinstance(parent, BlockItem):
                return parent
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            block = self._find_block_at(event.scenePos())
            if block and block._is_collapsible:
                # Check if click is on the collapse indicator (left portion of the block)
                local_x = event.scenePos().x() - block.pos().x()
                if local_x < BLOCK_STRIPE_W + 22:  # Stripe + indicator area
                    self.toggle_block_collapse(block.entry_index)
                    self.entry_clicked.emit(block.entry_index)
                    event.accept()
                    return

            if block and not block.is_expanded():
                self._drag_block = block
                self._drag_start_y = event.scenePos().y()
                self._drag_origin_index = block.entry_index
                self._drag_block_origin_pos = block.pos()
                self._drag_active = False
                self.entry_clicked.emit(block.entry_index)
            elif block and block.is_expanded():
                self.entry_clicked.emit(block.entry_index)
            else:
                self._drag_block = None
                # Clicked empty space - dim all connectors
                self.update_connector_highlights(-1)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_block and event.buttons() & Qt.LeftButton:
            delta = abs(event.scenePos().y() - self._drag_start_y)

            if not self._drag_active and delta > self.DRAG_THRESHOLD:
                # Start drag - collapse any expanded block first
                if self._expanded_index >= 0:
                    self.toggle_expand(self._expanded_index)
                self._drag_active = True
                self._drag_block.setOpacity(0.5)
                self._drag_block.setZValue(200)

                # Create drop indicator line
                self._drop_indicator = QGraphicsPathItem()
                pen = QPen(QColor("#528BFF"), 2.5)
                self._drop_indicator.setPen(pen)
                self._drop_indicator.setZValue(199)
                self.addItem(self._drop_indicator)

            if self._drag_active:
                # Move block with mouse
                new_y = event.scenePos().y() - (self._drag_block.height() / 2)
                self._drag_block.setPos(self._drag_block.pos().x(), new_y)

                # Calculate drop target
                self._update_drop_indicator(event.scenePos().y())

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._drag_active and self._drag_block:
            # Complete the drag
            self._drag_block.setOpacity(1.0)
            self._drag_block.setZValue(0)

            # Remove drop indicator
            if self._drop_indicator:
                self.removeItem(self._drop_indicator)
                self._drop_indicator = None

            # Execute the move if target is different from origin
            from_idx = self._drag_origin_index
            to_idx = self._drop_target_index

            if to_idx >= 0 and to_idx != from_idx:
                # Adjust: if moving down, the target shifts because the source is removed first
                if to_idx > from_idx:
                    to_idx -= 1
                self.entry_moved.emit(from_idx, to_idx)
            else:
                # Cancelled or same position - relayout to restore positions
                self._relayout()

            self._drag_active = False
            self._drag_block = None
            self._drag_origin_index = -1
            self._drop_target_index = -1
        elif self._drag_block and not self._drag_active:
            # Was a click, not a drag - already handled in mousePressEvent
            self._drag_block = None

        super().mouseReleaseEvent(event)

    def _update_drop_indicator(self, mouse_y: float):
        """Update the drop indicator line position based on mouse Y."""
        if not self._block_items:
            return

        # Find the gap closest to the mouse
        best_idx = 0
        best_dist = float('inf')

        for i, block in enumerate(self._block_items):
            if i == self._drag_origin_index:
                continue  # Skip the dragged block
            block_top = block.pos().y() if block != self._drag_block else self._drag_block_origin_pos.y()
            dist = abs(mouse_y - block_top)
            if dist < best_dist:
                best_dist = dist
                best_idx = i

        # Also check after the last block
        if self._block_items:
            last = self._block_items[-1]
            if last != self._drag_block:
                last_bottom = last.pos().y() + last.height()
            else:
                last_bottom = self._drag_block_origin_pos.y() + last.height()
            dist = abs(mouse_y - last_bottom)
            if dist < best_dist:
                best_idx = len(self._block_items)

        self._drop_target_index = best_idx

        # Draw indicator line at the target gap
        if best_idx < len(self._block_items):
            target_block = self._block_items[best_idx]
            indicator_y = target_block.pos().y() - 2
            if target_block == self._drag_block and best_idx + 1 < len(self._block_items):
                indicator_y = self._block_items[best_idx + 1].pos().y() - 2
        else:
            last = self._block_items[-1]
            indicator_y = last.pos().y() + last.height() + 2

        path = QPainterPath()
        path.moveTo(10, indicator_y)
        path.lineTo(BLOCK_WIDTH, indicator_y)

        # Arrow head
        path.moveTo(10, indicator_y)
        path.lineTo(18, indicator_y - 4)
        path.moveTo(10, indicator_y)
        path.lineTo(18, indicator_y + 4)

        self._drop_indicator.setPath(path)

    def mouseDoubleClickEvent(self, event):
        if self._drag_active:
            return  # Don't expand during drag

        block = self._find_block_at(event.scenePos())
        if block:
            self.toggle_expand(block.entry_index)
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)


#
# Block View Widget
#

class BlockView(QGraphicsView):
    entry_clicked = Signal(int)
    param_changed = Signal(int, int, int)
    entry_moved = Signal(int, int)  # from_idx, to_idx

    def __init__(self, model, main_window=None, parent=None):
        super().__init__(parent)
        self.model = model
        self._main_window = main_window
        self._selected_index = -1

        self._scene = BlockScene(model)
        self._scene.entry_clicked.connect(self._on_scene_click)
        self._scene.param_changed.connect(self.param_changed.emit)
        self._scene.entry_moved.connect(self.entry_moved.emit)
        self.setScene(self._scene)

        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.setStyleSheet("QGraphicsView { background-color: #21252B; border: none; }")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setDragMode(QGraphicsView.ScrollHandDrag)

    def _on_scene_click(self, index):
        self._selected_index = index
        self._scene.update_connector_highlights(index)
        self.entry_clicked.emit(index)

    def rebuild(self):
        self._scene.rebuild()

    def refresh_block(self, index):
        """Update a single block's display without full rebuild."""
        self._scene.refresh_block(index)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            # Zoom with Ctrl+Wheel
            delta = event.angleDelta().y()
            if delta > 0:
                factor = 1.1
                zoom_delta = 1
            else:
                factor = 0.9
                zoom_delta = -1

            # Apply zoom centered on mouse position
            self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
            self.scale(factor, factor)
            self.setTransformationAnchor(QGraphicsView.AnchorViewCenter)

            # Update the block zoom delta in the main window's settings
            if self._main_window and hasattr(self._main_window, '_settings'):
                main_window = self._main_window
                current_delta = main_window._settings.get("block_zoom_delta", 0)
                main_window._settings["block_zoom_delta"] = current_delta + zoom_delta
                main_window._update_zoom_label()

            event.accept()
        else:
            # Default scrolling behavior
            super().wheelEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self._move_selection(-1)
        elif event.key() == Qt.Key_Down:
            self._move_selection(1)
        elif event.key() == Qt.Key_Left and event.modifiers() & Qt.AltModifier:
            self._jump_same_type(-1)
        elif event.key() == Qt.Key_Right and event.modifiers() & Qt.AltModifier:
            self._jump_same_type(1)
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Enter also toggles expand
            if self._selected_index >= 0:
                self._scene.toggle_expand(self._selected_index)
        elif event.key() == Qt.Key_Escape:
            # Collapse any expanded block
            if self._scene._expanded_index >= 0:
                self._scene.toggle_expand(self._scene._expanded_index)
        else:
            super().keyPressEvent(event)

    def _move_selection(self, delta):
        count = self.model.count()
        if count == 0:
            return
        new_idx = max(0, min(count - 1, self._selected_index + delta))
        if new_idx != self._selected_index:
            self.highlight_entry(new_idx)
            self._selected_index = new_idx
            self._scene.update_connector_highlights(new_idx)
            self.entry_clicked.emit(new_idx)

    def _jump_same_type(self, direction):
        if self._selected_index < 0 or self._selected_index >= self.model.count():
            return
        target_type = self.model.entry(self._selected_index).event_type
        count = self.model.count()
        i = self._selected_index + direction
        while 0 <= i < count:
            if self.model.entry(i).event_type == target_type:
                self.highlight_entry(i)
                self._selected_index = i
                self._scene.update_connector_highlights(i)
                self.entry_clicked.emit(i)
                return
            i += direction

    def highlight_entry(self, index):
        items = self._scene._block_items
        if 0 <= index < len(items):
            for item in items:
                item.setSelected(False)
            items[index].setSelected(True)
            self.centerOn(items[index])

    def set_show_connectors(self, show: bool):
        self._scene.show_connectors = show
        self._scene._relayout()