"""
FE3H Event Script Editor - Control Flow Analysis
Identifies nesting depth, linked opcodes, and queue-mode blocks.

IMPORTANT: Queue blocks (135) are not nesting blocks. The game commonly uses
Begin Animation Queue without a matching Commit - the queue is implicitly
flushed by the dialogue tick or by the next Begin. Only conditionals and
subroutines create true nesting.
"""

from dataclasses import dataclass, field
from typing import Optional

#
# Control-flow opcode classification
#

# Only opcode 35 and opcodes 125-128 create IF/ELSE/END blocks.
CONDITIONAL_OPENERS = {35, 125, 126, 127, 128}
CONDITIONAL_ELSE = 37
CONDITIONAL_END = 36

SUB_CALL = 40
SUB_RETURN = 41
SUB_SKIP = 42

QUEUE_BEGIN = 135
QUEUE_COMMIT = 138

# Opcodes buffered inside a 135..138 queue window
QUEUE_BUFFERED = {11, 17, 23, 24, 66, 67, 69, 91, 94, 96, 98, 102, 103, 104}
QUEUE_PASSTHROUGH = {3, 9, 79, 81, 138}

#
# Linkage definitions
#

ARM_OPCODES = {130, 123, 118}
VOICE_COMMIT_OPCODES = {33, 34, 89}

POSITIONAL_PAIRS = {
    93: 29, 148: 107, 147: 95,
}

DIALOGUE_FLOW = {89, 33, 34, 3, 81, 90, 113}
BODY_TURN_GROUP = {6, 7, 67, 97}
BGM_GROUP = {15, 16, 52, 114, 133}
AUDIO_PAN_GROUP = {27, 38, 59, 30}
CAMERA_POS_GROUP = {140, 100}
AMBIENT_POS_GROUP = {141, 112}
SCENE_INIT_GROUP = {0, 1, 4, 5}
ANIM_TRIGGER_GROUP = {107, 108, 148}

GROUP_COLORS = {
    "arm_commit":     "#E06C75",
    "voice_commit":   "#E06C75",
    "dialogue_flow":  "#61AFEF",
    "body_turn":      "#C678DD",
    "bgm":            "#98C379",
    "audio_pan":      "#D19A66",
    "camera_pos":     "#56B6C2",
    "ambient_pos":    "#56B6C2",
    "scene_init":     "#ABB2BF",
    "anim_trigger":   "#E5C07B",
    "queue_buffered": "#C678DD",
    "queue_block":    "#C678DD",
}


@dataclass
class FlowInfo:
    """Per-entry flow analysis result."""
    indent: int = 0
    is_opener: bool = False
    is_closer: bool = False
    is_else: bool = False
    block_partner: Optional[int] = -1
    in_queue: bool = False
    link_group: Optional[str] = None
    link_partners: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


def analyze_control_flow(entries) -> list[FlowInfo]:
    """
    Analyze a list of ScriptEntry objects for control flow structure.
    Returns a FlowInfo per entry.
    """
    n = len(entries)
    info = [FlowInfo() for _ in range(n)]

    # Nesting (conditionals + subroutines only)
    # Queue blocks do NOT create nesting - the game uses them without matching commits.
    indent_stack = []  # stack of (opener_index, type)
    current_indent = 0

    for i, entry in enumerate(entries):
        et = entry.event_type

        if et == CONDITIONAL_ELSE:
            info[i].is_else = True
            if indent_stack and indent_stack[-1][1] == "cond":
                current_indent -= 1
                info[i].indent = current_indent
                info[i].block_partner = indent_stack[-1][0]
                current_indent += 1
            else:
                info[i].indent = current_indent
                info[i].warnings.append("ELSE without matching IF")

        elif et == CONDITIONAL_END:
            info[i].is_closer = True
            if indent_stack and indent_stack[-1][1] == "cond":
                opener_idx = indent_stack.pop()[0]
                current_indent -= 1
                info[i].indent = current_indent
                info[i].block_partner = opener_idx
                info[opener_idx].block_partner = i
            else:
                info[i].indent = current_indent
                info[i].warnings.append("END without matching IF")

        elif et in CONDITIONAL_OPENERS:
            info[i].is_opener = True
            info[i].indent = current_indent
            indent_stack.append((i, "cond"))
            current_indent += 1

        elif et == SUB_CALL:
            info[i].is_opener = True
            info[i].indent = current_indent
            indent_stack.append((i, "sub"))
            current_indent += 1

        elif et == SUB_RETURN:
            info[i].is_closer = True
            if indent_stack and indent_stack[-1][1] == "sub":
                opener_idx = indent_stack.pop()[0]
                current_indent -= 1
                info[i].indent = current_indent
                info[i].block_partner = opener_idx
                info[opener_idx].block_partner = i
            else:
                info[i].indent = current_indent
                info[i].warnings.append("RETURN without matching CALL")
        else:
            info[i].indent = current_indent

    # Mark unclosed blocks (only for conditionals/subs, not queues)
    for idx, btype in indent_stack:
        info[idx].warnings.append(f"Unclosed {btype} block")

    # Queue tracking (flat, no nesting)
    # Queue mode is a simple on/off state. A new 135 implicitly closes the previous.
    # In practice, the engine auto-flushes queues via the dialogue tick mechanism,
    # so scripts commonly use 135 without a matching 138. We only flag "dropped"
    # warnings inside explicit 135->138 pairs.
    queue_start = -1
    has_explicit_commit = set()  # queue openers that have a matching 138

    # Pre-scan: find which 135s have a 138 before the next 135
    temp_start = -1
    for i, entry in enumerate(entries):
        if entry.event_type == QUEUE_BEGIN:
            temp_start = i
        elif entry.event_type == QUEUE_COMMIT and temp_start >= 0:
            has_explicit_commit.add(temp_start)
            temp_start = -1

    for i, entry in enumerate(entries):
        et = entry.event_type

        if et == QUEUE_BEGIN:
            queue_start = i
            info[i].link_group = "queue_block"

        elif et == QUEUE_COMMIT:
            info[i].link_group = "queue_block"
            if queue_start >= 0:
                info[queue_start].block_partner = i
                info[i].block_partner = queue_start
                info[i].link_partners.append(queue_start)
                info[queue_start].link_partners.append(i)
            queue_start = -1

        elif queue_start >= 0:
            info[i].in_queue = True
            if et in QUEUE_BUFFERED:
                info[i].link_group = "queue_buffered"
            elif et in QUEUE_PASSTHROUGH:
                pass
            elif queue_start in has_explicit_commit:
                # Only warn inside explicit 135->138 windows
                info[i].warnings.append("Dropped in queue mode")

    #
    # Linkage analysis
    #

    # ARM -> COMMIT
    for i, entry in enumerate(entries):
        if entry.event_type in ARM_OPCODES:
            info[i].link_group = "arm_commit"
            for j in range(i + 1, n):
                if entries[j].event_type in VOICE_COMMIT_OPCODES:
                    info[i].link_partners.append(j)
                    info[j].link_partners.append(i)
                    if not info[j].link_group:
                        info[j].link_group = "voice_commit"
                    break

    # Positional pairs
    for i, entry in enumerate(entries):
        if entry.event_type in POSITIONAL_PAIRS:
            target_type = POSITIONAL_PAIRS[entry.event_type]
            for j in range(i + 1, min(i + 5, n)):
                if entries[j].event_type == target_type:
                    info[i].link_partners.append(j)
                    info[j].link_partners.append(i)
                    break

    # Group coloring
    group_map = [
        ("dialogue_flow", DIALOGUE_FLOW),
        ("body_turn", BODY_TURN_GROUP),
        ("bgm", BGM_GROUP),
        ("audio_pan", AUDIO_PAN_GROUP),
        ("camera_pos", CAMERA_POS_GROUP),
        ("ambient_pos", AMBIENT_POS_GROUP),
        ("scene_init", SCENE_INIT_GROUP),
        ("anim_trigger", ANIM_TRIGGER_GROUP),
    ]
    for i, entry in enumerate(entries):
        if info[i].link_group:
            continue
        for gname, gset in group_map:
            if entry.event_type in gset:
                info[i].link_group = gname
                break

    return info
