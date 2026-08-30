# FE3H: Event Scripting Tool
# Event opcode definitions only

# Load the custom "event-enums.py"
import event_enums as enums

######################################
### Event opcode info
######################################

# Control-flow opcode commands are all caps (the dispatcher ignores all parameters for them, they can be used for more advanced scripting)
# Certain opcodes remain completely unused in the game scripts (but might still work when it's called by them)
# Reason why some may not be present in the scripts is because those are used by the internal compiler/editor only (or there was no need to use them)

# There are also some missing opcodes (no idea if they do anything at all): 44, 151, 152
# STUB_ADVANCE is the same action for opcode commands: 14, 21, 39, 48, 50, 55, 56, 58, 62, 68, 70, 72, 74, 75, 76, 77, 92, 111, 117

# There are some alias opcode variants (same functions, but sometimes with slight changes):
# 3, 81    -> has function differences (see their opcodes)
# 4, 139   -> has function differences (see their opcodes)
# 12, 78   -> no differences
# 18, 105  -> has function differences (see their opcodes)
# 19, 106  -> no differences
# 142, 143 -> no differences

# Some of these opcodes have a unified functionality (two layers) in the command dispatcher:
#
# A. Audio layer:
# 9 - JUMP_EOF
# 43 - Character Volume Fade
# 78 - ADVANCE_SEQUENCER
# 85 - Channel Mask Override
# 95 - Assign Ambient Sound Slot
# 130 - SET_FLAG_3D
# 147 - NOOP
#
# B. Gameplay layer:
# 9 - House Selection Event
# 43 - Character Visibility
# 78 - Recruitment List
# 85 - Set Dialogue Behaviour
# 95 - Give Item To Character
# 130 - Fancy Dialogue Choice Menu
# 147 - Load Item

# Some of these could still have dual-purposes, if so, you'll see the audio layer definition itself, while the gameplay one needs testing to know what it is

######################################
### Event names
######################################

event_names = {
    0: "Cube Scene Init",            # Stalls until scene load is complete
    1: "Character List",
    2: "STALL_SEQUENCER",            # Hard sequencer stall. It sets active=0 and returns immediately
    3: "Dialogue Box",
    4: "Scene Event",
    5: "Scene Character Event",
    6: "Body Turn Y",
    7: "Body Turn X",
    8: "CONTINUE",
    9: "House Selection Event",      # JUMP_EOF
    10: "Set Node Transform",        # Sets position/rotation for characters, cameras, or effect nodes
    11: "Animation",
    12: "ADVANCE_SEQUENCER",         # Makes the sequencer progress. It sets active=1 and returns immediately
    13: "WAIT",
    14: "STUB_ADVANCE",
    15: "BGM Switch",
    16: "BGM Fade Out",
    17: "Sound Effect",
    18: "Image Card (In-Scene)",
    19: "Update Mouth Animation",    # DialogueBox_UpdateMouthState - updates lip-sync state for current voice line
    20: "Voice Stop",                # Stops active voice stream playback for a given channel ID 
    21: "STUB_ADVANCE",
    22: "SFX Fade Out",
    23: "Body Motion",
    24: "Head Motion X",
    25: "Screen Transition",
    26: "Set Character Layout Preset", # Scene layout/spatial preset applicator
    27: "Audio Pan Oscillation Set A", # For the amplitude
    28: "Character Layout Positions",
    29: "Assign Character Slot",
    30: "Set Audio Pause",           # Sets AudioMixer pause flag; p1=0 to unpause, p1=1 to pause; also clears camera state on unpause
    31: "Listener Rotation Tween Setup",
    32: "Set Dialogue Line",         # UNUSED BY SCRIPTS - primes speaker index before voice play (opcode 3/81). Stalls until voice allocation resolves.
    33: "Dialogue 2-Choice Menu",
    34: "Dialogue 3-Choice Menu",
    35: "CONDITIONAL STATEMENT",
    36: "CONDITIONAL END",
    37: "CONDITIONAL ELSE",
    38: "Audio Pan Oscillation Set B", # For the cycle count
    39: "STUB_ADVANCE",
    40: "SUB_CALL",                  # Pushes current PC to call stack, jumps to target (no params)
    41: "SUB_RETURN",                # Pops PC from call stack (no params)
    42: "SKIP_SUB",                  # scans forward past matching RETURN, skips entire sub body (no params)
    43: "Character Visibility And Volume Fade",
    #44 is missing (not in audio layer) - never called from scripts, may still have an unknown gameplay function though
    45: "Support Point Modifier",
    46: "Set Event Flag",            # Sets/clears a persistent event condition flag
    47: "Load Scene Layout",         # UNUSED BY SCRIPTS - Internal: loads camera/layout preset & resets audio pipeline
    48: "STUB_ADVANCE",
    49: "Audio Reset",               # Resets the audio pipeline & envelope defaults (clean up audio state if BGM/ambience bleeds between scenes)
    50: "STUB_ADVANCE",
    51: "Set 3D Audio Mode",         # UNUSED BY SCRIPTS - configures surround/stereo routing priority for 11 voice channels
    52: "BGM Layer Swap",            # Swaps active BGM variant/layer in-place
    53: "Set Focal Channel",         # UNUSED BY SCRIPTS - sets focal character for spatial audio routing
    54: "Camera 2-Char Focus",
    55: "STUB_ADVANCE",
    56: "STUB_ADVANCE",
    57: "Stop Character Voice",      # Forces immediate voice stop & channel reset (might be used when cutting someone's speech abruptly)
    58: "STUB_ADVANCE",
    59: "Audio Pan Sweep",
    60: "Set Battle Voice Variant",  # UNUSED BY SCRIPTS - this does nothing here, only works in battle scenes (changes Byleth's voice banks to the alternate variants)
    61: "Activate Channel Audio Object", # UNUSED BY SCRIPTS
    62: "STUB_ADVANCE",
    63: "Update Character Spatial Audio", # UNUSED BY SCRIPTS
    64: "Set Character Body Position",
    65: "Audio Proximity Distance Threshold", # UNUSED BY SCRIPTS
    66: "Play SFX From Table",       # Reads 4-field packed SFX record from DAT_7100cee0b0[p2*0x10] and plays it on the character's voice channel
    67: "Set Body Facing Angle",
    68: "STUB_ADVANCE",
    69: "Head Motion Y",
    70: "STUB_ADVANCE",
    71: "Set Scene Anchor Position", # UNUSED BY SCRIPTS
    72: "STUB_ADVANCE",
    73: "Camera At Character",
    74: "STUB_ADVANCE",
    75: "STUB_ADVANCE",
    76: "STUB_ADVANCE",
    77: "STUB_ADVANCE",
    78: "Recruitment List",
    79: "CHARACTER_CHECK",
    80: "SUPPORT_LEVEL_CHECK",
    81: "Dialogue Box (Gated)",
    82: "PARTY_SIZE_CHECK",
    83: "Screen Overlay",
    84: "Reset Scene Systems",
    85: "Set Dialogue Properties",
    86: "Clear Frame State",         # Clears the fade timer, resets VoiceChannel animation, optionally submits an idle animation trigger, always stalls
    87: "Camera Movement",           # This camera movement is more like an instant snap
    88: "Camera Pan",                # This is a slow cinematic camera sweep (timed sweep)
    89: "Dialogue 1-Choice Menu",
    90: "DIALOGUE_PAGE_SEPARATOR",   # PAGE_TURN_MARKER - marks boundary between dialogue pages; triggers page-advance check in TalkEvent_Tick; stalls until player advances
    91: "All Look At Character",
    92: "STUB_ADVANCE",
    93: "Set Position Yaw Override",
    94: "Character Look At",
    95: "Give Item To Character",    # Dual-function: 1. Give Item To Character, 2. Assign Ambient Sound Slot 
    96: "Emote Effect",
    97: "WAIT_FOR_BODY_TURN",        # Sequencer sync point after triggering a body rotation with 67
    98: "Character Eyes",
    99: "Route Change",
    100: "Camera Move Direct",
    101: "Camera Layout Transition",
    102: "Set Voice Blend Mode",
    103: "Character Expression Mode",
    104: "Set Head And Body Orientation",
    105: "Image Card",
    106: "Update Mouth Animation",
    107: "Enqueue Animation Action",
    108: "Cancel Active AnimSeq Slots",
    109: "Set Scene Color RGB",
    110: "Cancel Emote Effects",
    111: "STUB_ADVANCE",
    112: "Set Ambient Layer Direction",
    113: "Load Dialogue Line",
    114: "Set BGM Variant B",
    115: "Refresh Character Audio Position",
    116: "Set Character Slot Idle",
    117: "STUB_ADVANCE",
    118: "Set Crossfade Slot Mode",
    119: "SELECT_CHANNEL",
    120: "END_OF_STEP",
    121: "Set Character Pair",
    122: "Set Camera Direction Override",
    123: "Suppress Next Audio Start",
    124: "CONDITIONAL_SLOT_RNG",          # Condition Slot RNG Init
    125: "CONDITIONAL_CHAR_ID",           # Conditional Branch by Character ID
    126: "CONDITIONAL_HOUSE_LORD_ID",     # Conditional Branch by House Lord Index
    127: "CONDITIONAL_BATTLE_COMPLETION", # Conditional Battle Completion
    128: "CONDITIONAL_FLAG_CHECK",        # Conditional Event Flag Check
    129: "Set Subtitle And Portrait Mode",
    130: "Fancy Dialogue Choice Menu",
    131: "Set Active Voice-Channel Roster",
    132: "Display Item Reward",
    133: "Preserve Music Flag",      # Keeps the music (BGM) playing
    134: "BodyTurn + CharActor Anim Coordinated Wait",
    135: "Begin Animation Queue",    # QUEUE_MODE - Enables command queuing: subsequent opcodes buffer into a ring (capacity 40) to fire in sync. p1=queue config arg. Causes "timed" animation/motion effect.
    136: "Screen Fade",
    137: "Animation Action Activation Pending?",
    138: "Commit Animation Queue",   # Commit Animation Queue
    139: "Scene Event (Reset Walk-In State)",
    140: "Camera Position",
    141: "Ambient Layer Position",
    142: "Character Walk-In Animation A",
    143: "Character Walk-In Animation B",
    144: "Voice 3D Pan",             # Sets 3D spatial position for a character's voice stream.
    145: "Camera Flip",
    146: "Change Cube Label To",     # Updates scene title label (location/time/month) and triggers BGM crossfade transition simultaneously
    147: "Load Item",                # Dual-functionality: Add Item and NOP
    148: "Anim Audio Continuity",
    149: "Set Ambient Volume",
    150: "Divine Pulse Increment",
    #151 is missing (not in audio layer) - never called from scripts, may still have an unknown gameplay function though
    #152 is missing (not in audio layer) - never called from scripts, may still have an unknown gameplay function though
    153: "Auto-Advance Delay",
    154: "Set Dimitri Angry State",  # PartyList_FindMemberSlot(slot=3=Dimitri) + clears bit1 of member+0xAE (party-available flag). Makes Dimitri unavailable/angry.
    155: "Store Channel A",          # UNUSED BY SCRIPTS - Internal channel registry/stash opcode, probably for engine/compiler bookkeeping commands
    156: "Store Channel B",          # UNUSED BY SCRIPTS - same as 155, but for the other channel
}

######################################
### Event parameter definitions
######################################

event_param_definitions = {
    0: {  # Cube Scene (initialize or setup cutscene)
        1: ("bg_img", enums.enumCubeScene),
        2: ("unknown", None),           # Always -1; probably a scene variant or more likely a scene exclusion/element selector (sentinel) that defaults to "no restriction".
        3: ("scene_render_mode", None), # Observed values: 0-5
                                        # Predefined layout configuration for rendering - i.e. what to display (and maybe audio spatialization).
                                        # Controls whether the background (cube scene) and 3D character model renders and how the camera is framed.
                                        # (Needs more testing to nail down the exact details, maybe camera/BG perspective- and/or audio-related)
                                        # 0: No 3D character(s) visible, but the background is visible
                                        # 1: Identical to 0, not sure about the difference
                                        # 2: 3D character(s) and the background are both visible
                                        # 3: Pure black background - transition state: no 3D character(s) and no background visible, portrait (dialogue box) only.
                                        # 4: Identical to 2, not sure about the difference
                                        # 5: For Sothis Throne scenes only
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    1: {  # Character List
        i: (f"char{i}", enums.enumCharacter) for i in range(1, 12)
    },
    2: {  # STALL_SEQUENCER, sets active=0
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    3: {  # Dialogue Box
        1: ("character", enums.enumCharacter),
        2: ("text_line", None),
        3: ("animation", enums.enumAnimation),
        4: ("portrait_expression", enums.enumPortraitExpression),
        5: ("voice_line", None),
        6: ("use_mouth", enums.enumBool), # if false, character's mouth will never open while speaking
        **{i: (f"param{i}", None) for i in range(7, 12)},
    },
    4: {  # Scene Event
        # Places characters who are already standing in their positions
        1: ("event_function", enums.enumSceneEvent),
        **{i: (f"char{i-1}", enums.enumCharacter) for i in range(2, 12)},
    },
    5: {  # Scene Character Event
        1: ("event_function", enums.enumSceneCharacterEvent),
        **{i: (f"char{i-1}", enums.enumCharacter) for i in range(2, 12)},
    },
    6: {  # Body Turn Y (Horizontal)
        1: ("turn_direction", enums.enumBodyTurnDir), # 0=turn right, 1=turn left, 2=passthrough (no-op)
        2: ("turn_mode", enums.enumBodyTurnMode),     # 0=async (clears script-wait), 1=blocking (keeps wait), 2=instant/special path
        3: ("duration_frames", None),           # Turn duration in frames (seconds internally, 1/60) or 0.5s default
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    7: {  # Body Turn X (Vertical)
        1: ("turn_direction", enums.enumBodyTurnDir),
        2: ("turn_mode", enums.enumBodyTurnMode),
        3: ("duration_frames", None),
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    8: {  # CONTINUE - forces active=1 and advances sequencer without executing logic
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    9: {  # House Selection Event | but before that: JUMP_EOF - jumps PC to total_command_count - 1; forces active=1
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    10: {  # Set Node Transform (Position/Rotation)
        # Binary: FUN_7100487b60. Applies 3D translation + rotation to target node.
        # p5 is converted to radians: p5 * 0.017453292 (degrees → radians)
        # p2/p3/p4 are signed offsets (large unsigned values in dump = negative coords)
        1: ("target_id", None),        # Node/Character/Camera ID to transform
        2: ("offset_x", None),         # X axis offset (float cast)
        3: ("offset_y", None),         # Y axis offset
        4: ("offset_z", None),         # Z axis offset
        5: ("rotation_deg", None),     # Rotation angle in degrees (radians internally)
        **{i: (f"param{i}", None) for i in range(6, 12)},
    },
    11: { # Animation
        # Used when character isn't speaking
        1: ("character", enums.enumCharacter),
        2: ("animation", enums.enumAnimation),
        3: ("layout_preset", None), # Scene layout / spatial preset index (0-13) or -1 - scripts use 0-8 only
        4: ("unknown", None),       # Maybe a sentinel
        5: ("hold_duration_frames", None),
        **{i: (f"param{i}", None) for i in range(6, 12)},
    },
    12: {  # ADVANCE_SEQUENCER - the opposite of opcode 2; forces active=1
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    13: { # WAIT (Pause for X frames)
        1: ("frames", None),
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    14: {  # STUB_ADVANCE
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    15: { # BGM Switch
        1: ("bgm_id", enums.enumBGM),
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    16: { # BGM Fade Out
        1: ("duration_frames", None), # in ms (* 1000/60)
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    17: { # SFX
        1: ("sfx", enums.enumSoundEffect),
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    18: { # Image Card (In-Scene)
        1: ("image_card", enums.enumCard),
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    19: {  # Update Mouth Animation
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    20: {  # Voice Stop
        1: ("channel_id", None),
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    21: {  # STUB_ADVANCE
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    22: {  # SFX Fade Out
        1: ("duration_frames", None), # Optional fade duration in frames (0-100 observed)
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    23: { # Body Motion
        1: ("character", enums.enumCharacter),
        2: ("direction_index", enums.enumBodyMotion),
        3: ("duration_frames", None),
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    24: { # Head Motion X
        1: ("character", enums.enumCharacter),
        2: ("direction_index", enums.enumHeadMotionX),
        3: ("duration_frames", None),
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    25: { # Scene Transition
        1: ("cube_scene", enums.enumCubeScene),
        2: ("channel_mask", None),                         # always 0xFFFFFFFF - no channel restriction
        3: ("scene_context", enums.enumAudioChannelBanks), # audio channel bank index: 5 simultaneous scene contexts
                                                           # set which 12-channel group the incoming scene's voices will use
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    26: {  # Set Character Layout Preset (Spatial/Camera Position)
        1: ("layout_preset", None),            # Scene layout / spatial preset index (0-13 only)
        2: ("character", enums.enumCharacter), # Character to apply preset to
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    27: {  # Audio Pan Oscillation Set A
        # This sets the "how far" (amplitude) part of it.
        # Note: Set A and Set B (38) must be paired - A sets amplitude, B accumulates the phase that the renderer uses for sin().
        1: ("audio_channel", enums.enumAudioPanChannels),  # routing mode: 1=right, 2=left
        2: ("duration_frames", None),                      # transition duration in frames (observed as 15-1500)
        3: ("pan_amplitude", None),                        # target pan position in units; always positive
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    28: {  # Character Layout Positions - sets initial scene layout offsets
        # "-1" means "don't update this slot", so it passes through as-is, leaving the slot at whatever value it had before.
        # This declares where everyone stands.
        **{i: (f"pos_{i}", None) for i in range(1, 12)},
    },
    29: {  # Assign Character Slot - this moves one character into the specified layout/position (with full 3D placement).
        1: ("character", enums.enumCharacter),
        2: ("position_index", None),   # Layout/position index offset (0-11) | this is the relative value within the current layout group
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    30: {  # Set Audio Pause - toggles AudioMixer pause flag
        1: ("paused", enums.enumBool),   # 0=unpause, 1=pause
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    31: {  # Listener Rotation Tween Setup
        # Rotates the listener position in 3D space.
        # This is subtle scene "breathing" - slowly rotating the listening direction during long dialogue.
        1: ("rotation_channel", enums.enumAudioTween),  # 1 or 2 = Rotation Tween Block A, 3 or 4 = Rotation Tween Block B
                                                        # 0 or >= 5 is reset (zeroes both channels), but >=5 Block A remaining/total/amplitude aren't cleared
                                                        # only mode=0 clears it
        2: ("duration_frames", None),                   # Rotation duration in frames
        3: ("target_value", None),                      # Rotation amplitude: default 0 = 3.0 (about 3 degrees of rotation, stored as float)
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    32: {  # Set Dialogue Line - VoiceChannel_SetDialogueLine; primes speaker before opcode 3
        # p1 MUST be 0 (primary voice slot). Only fires when p1==0.
        # p2 is KTSL2-internal speaker index, NOT the same as enums.enumCharacter.
        # Stalls sequencer (active=0) after executing.
        1: ("slot", None),          # must be 0 for primary voice slot
        2: ("speaker_idx", None),   # KTSL2 internal speaker index
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    33: {  # Dialogue 2-Choice Menu
        1: ("choice_var_id", None),       # Gating ID for dialogue advancement state machine
        2: ("text_id_slot1", None),       # First allocated text index ID
        3: ("text_id_slot2", None),       # Second allocated text index ID
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    34: {  # Dialogue 3-Choice Menu
        # Identical to 33 but allocates 3 text IDs. Used for multi-speaker choice menus.
        1: ("choice_var_id", None),       # Gating ID for dialogue advancement
        2: ("text_id_slot1", None),       # First allocated text index ID
        3: ("text_id_slot2", None),       # Second allocated text index ID
        4: ("text_id_slot3", None),       # Third allocated text index ID
        **{i: (f"param{i}", None) for i in range(5, 12)},
    },
    35: { # Conditional Statement
        # conditional_type can be 0-9, and their "expected_value" (param2) and "index" (param3) may be the following:
        # 0: Script_Variable_Check (often for dialogues) | param2 = expected value (0-3 = choice), param3 = index into TalkEvent_Context+0x6740 table
        # 1: Byleth_Gender_Check | param2 = expected gender (0=male, 1=female), param3 = UNUSED (overwritten internally)
        # 2: Item_Possession_Check | param2 = 0 (don't have) / 1 (have), param3 = item flag index (< 61)
        # 3: Condition_Slot_Nonzero | param2 = 0 or nonzero (>0 check), param3 = TrackState+0x154 slot index
        # 4: Route_Or_Chapter_State | param2 = expected route/chapter value (0-3), param3 = UNUSED (world+0x2449E read directly)
        # 5: Chapter_Progress_Flag | param2 = 0 or 1 (progress flag state), param3 = UNUSED
        # 6: Event_Or_Story_Flag | param2 = 0 (not set) / 1 (set), param3 = event flag ID
        # 7: Relationship_S-Rank_Check_CharSource | param2 = expected state, param3 = support pair index (-> falls into 8)
        # 8: Relationship_S-Rank_Check_CharDest   | param2 = 0 or 1 (level==4 S-Rank Check), param3 = character/relationship index
        # 9: Condition_Slot_Exact_Match | param2 = exact value to match (==, not >0), param3 = TrackState+0x154 slot index;
        # 10+: Early_Return | no-op, returns immediately
        1: ("conditional_type", enums.enumConditionalType),
        2: ("expected_value", None), # expected/compare value (what the condition tests against)
        3: ("index", None),          # index or subject_id (what is being checked)
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    36: {i: (f"param{i}", None) for i in range(1, 12)},  # Conditional End
    37: {i: (f"param{i}", None) for i in range(1, 12)},  # Conditional Else
    38: {  # Audio Pan Oscillation Set B
        # This sets the "how many times" (cycle count) part of it.
        # Note: Set A and Set B (38) must be paired - A sets amplitude, B accumulates the phase that the renderer uses for sin().
        1: ("mode", enums.enumAudioOscillation), # observed: 1-2; 1 = negative phase (CCW), 2 = positive phase (CW)
        2: ("duration_frames", None),            # observed: 150–3000 frames; tween duration
        3: ("oscillation_cycles", None),         # observed: 1-15; confirmed to be between 0.10–2.00 Hz; number of complete pan oscillation cycles over the duration
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    39: {  # STUB_ADVANCE
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    40: {  # CALL (Subroutine Call)
        # BINARY NOTE: Core bytecode instruction. Pushes current PC (param_1[2]) 
        # onto the call stack at +0x198, increments stack pointer at +0x194.
        # Does NOT jump immediately. Execution continues linearly into the subroutine.
        # Paired with 41 (RETURN) to pop PC and resume after the subroutine.
        # Ignores all parameters (hence all zeros in dump).
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    41: {  # RETURN - pops PC from call stack, decrements stack pointer. Resumes execution after subroutine.
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    42: {  # SKIP_SUB - scans forward past matching RETURN (0x29). Used by editor/compiler to skip subroutine bodies.
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    43: { # Character Visibility And Volume Fade
        1: ("character", enums.enumCharacter),
        2: ("visibility_and_volume_on", enums.enumBool),
        3: ("audio_duration_frames", None), # audio fade duration in frames - in scripts it's always 0 (instant)
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    45: {  # Support Point Modifier - modifies support rank
        # param1 = target character channel
        # param2 = 0 = Gain, 1 = Loss (sign flip)
        # param3 = point magnitude tier: 0 or 1=Standard, 2=Medium, 3=Major, 4+=No Change
        1: ("support_character", enums.enumCharacter),
        2: ("direction", enums.enumSupportPoints),                # 0 = Gain, 1 = Loss
        3: ("point_magnitude", enums.enumSupportPointMagnitude),  # 1, 2, or 3 (hardcoded tier), 2 was never used in scripts - any other value means no support change
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    46: { # Set Event Flag
        # Checked by opcode 128
        1: ("enabled", enums.enumFlagSet46),  # 0=clear the flag, 1=set the flag
        2: ("flag_id", enums.enumEventFlags), # event condition flag ID
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    47: {  # LOAD_SCENE_LAYOUT - internal engine command for scene/camera layout + audio pipeline reset
        # Used only when setting up a scene from scratch (hence the pipeline reset)
        # For running scenes, use 26 to reposition a character's spatial audio instead
        1: ("layout_preset", None),    #  indexes into DAT_7100cec130[scene_context][preset]
        2: ("position_offset", None),  # -1 uses preset's embedded position; any other value overrides from the layout position table
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    48: {  # STUB_ADVANCE
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    49: {  # AUDIO_RESET - TalkEvent_Context_ResetPipelineAndPrepare(AudioMixer, 1)
        # Wipes 7-stage signal pipeline (+0x1D0..+0x468), resets envelope defaults (+0x484..+0x4BC),
        # clears reverb flags, and pre-ticks timers. Use before major BGM transitions or scene loads.
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    50: {  # STUB_ADVANCE
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    51: {  # Set 3D Audio Mode - configures surround/stereo routing priority for 11 voice channels
        # Note: unknown mode values (anything not 0/1/2) silently skip all writes but still advance the sequencer - no hang, no error.
        1: ("mode", enums.enum3DAudioMode), # 0 = Off, 1 = Stereo, 2 = Surround
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    52: {  # BGM Layer Swap - swaps active BGM variant/layer in-place
        1: ("layer_index", None), # 1-4 only
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    53: {  # Set Focal Channel - sets focal character for spatial audio routing
        1: ("id", None), # character or channel ID - this is a short (like channel IDs), not an int
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    54: { # Camera 2-Char Focus - positions camera midpoint between two characters & applies pan tween
        # Computes 3D midpoint between char1 & char2, updates camera target.
        # camera_pos sets initial rotation offset relative to the pair.
        # panning sets tween direction. -1 skips panning entirely.

        # Note 1:
        # The camera target (what it looks at) is the exact midpoint between the two characters.
        # But the camera position is not at the midpoint, it's placed 250 units past character2_front in the character1_back to character2_front direction.
        # So character2_front is always the "near" character whose back faces the camera, and character1_back is always the "far" character we're looking at past them.
        # The naming _back and _front refers to their relationship to the camera, and not to each other.

        # Note 2:
        # Pan speed for modes 4 and 5 is distance-proportional (dist * 30 / constant), while modes 0–3 use a fixed speed of 30.
        # So "Pan_Down_In" and "Pan_Down_In_Alt" automatically scale their movement to the distance between the two characters:
        # closer characters pan faster, farther characters pan slower.

        1: ("character1_back", enums.enumCharacter),
        2: ("character2_front", enums.enumCharacter),
        3: ("camera_pos", enums.enumCameraPos54),
        4: ("panning", enums.enumCameraPan54),
        **{i: (f"param{i}", None) for i in range(5, 12)},
    },
    55: {  # STUB_ADVANCE
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    56: {  # STUB_ADVANCE
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    57: {  # Stop Character Voice
        # Forces immediate voice termination & channel reset. Does not stall sequencer.
        1: ("character", enums.enumCharacter),
        2: ("padding", None), # Unused by engine; usually 1 or sometimes 2 in compiled scripts
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    58: {  # STUB_ADVANCE
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    59: {  # Audio Pan Sweep
        1: ("_unused", None),           # no channel selector for sweeps
        2: ("duration_frames", None),   # observed: 60–2000 frames; sweep duration
        3: ("pan_from", None),          # signed s16 to float; observed: −140 to +225; neg=left-of-center, pos=right-of-center, 0=return-to-center
        4: ("pan_to", None),            # signed s16 to float; observed: −45 to +150; neg=left-of-center, pos=right-of-center, 0=return-to-center
                                        # pan_from == pan_to (same nonzero): hold at that position (no net movement).
        **{i: (f"param{i}", None) for i in range(5, 12)},
    },
    60: {  # Set Battle Voice Variant
        # Does not work in cutscene events, only in battle scenes
        1: ("alternate_banks_enabled", enums.enumBool), # 0 = default Byleth voice banks (0x22A/0x230), any nonzero value = alternate banks (0x22B/0x231)
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    61: {  # Activate Channel Audio Object
        1: ("_unused", None), # always 0 or padding
        2: ("character_id", enums.enumCharacter), # the character/channel whose audio object to activate
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    62: {  # STUB_ADVANCE
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    63: { # Update Character Spatial Audio
        1: ("character", enums.enumCharacter),
        2: ("spatial_mode", enums.enumCharSpatialAudio),
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    64: { # Set Character Body Position
        1: ("character", enums.enumCharacter),
        2: ("pos_x", None),
        3: ("pos_y", None),
        4: ("pos_z", None),
        **{i: (f"param{i}", None) for i in range(5, 12)},
    },
    65: { # Audio Proximity Distance Threshold
        1: ("proximity_threshold", None), # (int cast to float on write)
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    66: {  # Play SFX From Table - reads packed 4-field SFX record from DAT_7100cee0b0
        # Different from 17 which goes through the abstract ID to internal ID mapping chain
        # This goes directly to a pre-packed record
        1: ("character", enums.enumCharacter),    # character channel to play on
        2: ("table_index", None),                 # multiplied by 0x10 (16) to get the byte offset into the packed SFX table
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    67: { # Set Body Facing Angle
        1: ("character", enums.enumCharacter),
        2: ("angle_table_idx", None), # the rotation table: direction vector is (sin, 0, cos) - rotation around the Y axis in the XZ plane
        3: ("duration_frames", None), # 1/60
        4: ("direction", enums.enumRotation),
        **{i: (f"param{i}", None) for i in range(5, 12)},
    },
    68: {  # STUB_ADVANCE
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    69: { # Head Motion Y
        # Behaviour notes in comparison to 24:
        # 1. No negation. "Head Motion X" applies -(angle * π/180) before writing, "Head Motion Y" applies +(angle * π/180) directly.
        # Positive indices mean "up" here without the sign flip.
        # 2. Asymmetric clamp. "Head Motion X" clamps to ±45° symmetrically. "Head Motion Y" only clamps the upper bound to DAT_7100cb7da8
        # The lower bound is unclamped, so downward tilts (negative indices 4–6) have more freedom.
        1: ("character", enums.enumCharacter),
        2: ("direction_index", enums.enumHeadMotionY),
        3: ("duration_frames", None),
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    70: {  # STUB_ADVANCE
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    71: { # Set Scene Anchor Position
        # The scene anchor (XYZ world position) simultaneously drives:
        # 1. Where the camera is positioned/targeted
        # 2. Where all 11 character slots are anchored
        # 3. The audio source distance for talk event volume attenuation
        # This manually overrides what the layout table would otherwise set automatically.
        1: ("_unused", None), # completely unused
        2: ("pos_x", None),
        3: ("pos_y", None),
        4: ("pos_z", None),
        **{i: (f"param{i}", None) for i in range(5, 12)},
    },
    72: {  # STUB_ADVANCE
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    73: { # Camera At Character
        1: ("camera_pos", enums.enumCameraPos),
        2: ("character", enums.enumCharacter),
        3: ("panning", enums.enumCameraPan),
        4: ("unknown", None), # usually -1, but can also be 0-2 - probably a sentinel? (-1: no exclusion) - does nothing for the audio layer, not sure about the gameplay one
        **{i: (f"param{i}", None) for i in range(5, 12)},
    },
    74: {  # STUB_ADVANCE
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    75: {  # STUB_ADVANCE
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    76: {  # STUB_ADVANCE
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    77: {  # STUB_ADVANCE
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    78: { # Recruitment List
        # Dual-purpose function: for the audio layer, this advances the sequencer.
        # So it doesn't stall the audio thread while the gameplay UI runs.
        **{i: (f"char{i}", enums.enumCharacter) for i in range(1, 9)},
        **{i: (f"param{i}", None) for i in range(10, 12)},
    },
    79: { # Character Check
        1: ("conditional_slot", None),
        2: ("char_status", enums.enumCharStatus),
        **{i: (f"char{i}", enums.enumCharacter) for i in range(3, 12)},
    },
    80: { # Support Level Check
        1: ("conditional_slot", None),
        2: ("src_char", enums.enumCharacter),
        3: ("dest_char", enums.enumCharacter), # or -1 = scan all partners/supports
        4: ("rank_threshold", enums.enumSupportRanks),
        5: ("comparison_op", enums.enumComparisonOp),
        **{i: (f"param{i}", None) for i in range(6, 12)},
    },
    81: {  # Dialogue Box (Gated)
        # Same as opcode 3, it just adds the channel-exclusion pre-check at the top,
        # and inside DispatchVoice, the cmd[0] != 0x51 guard enables the gate logic (param7)
        # This is a cool thing that remained unused in the scripts, but the idea for the gate logic is like this:
        #
        # Condition Slot RNG Init(slot=0, max=3)   -- slot[0] = 0, 1, or 2
        # Condition Slot RNG Init(slot=1, max=2)   -- slot[1] = 0 or 1
        # Dialogue [3] "Main line - always plays."
        # Dialogue [81, condition_slot_gate_idx=0] "Extra quip - plays 2/3 of the time."
        # Dialogue [81, condition_slot_gate_idx=1]  "Second optional line - plays 1/2 of the time."
        #
        # The gate is for independent per-line suppression (each line plays or doesn't on its own roll),
        # while Condition_Slot_Exact_Match + conditional blocks is for mutually exclusive selection (exactly one of N lines plays).
        # To put it simple, if an additional dialogue is needed (that doesn't always need to play), the gating logic can be used
        1: ("character", enums.enumCharacter),
        2: ("text_line", None),
        3: ("animation", enums.enumAnimation),
        4: ("portrait_expression", enums.enumPortraitExpression),
        5: ("voice_line", None),
        6: ("use_mouth", enums.enumBool), # if false, character's mouth will never open while speaking
        7: ("condition_slot_gate_idx", enums.enumSuppressDialogueVoice),
        **{i: (f"param{i}", None) for i in range(8, 12)},
    },
    82: { # Party Size Check
        1: ("party_count_threshold", None),
        2: ("comparison_op", enums.enumComparisonOp),
        3: ("excluded_char1", enums.enumCharacter),
        4: ("excluded_char2", enums.enumCharacter),
        5: ("excluded_char3", enums.enumCharacter),
        **{i: (f"param{i}", None) for i in range(6, 12)},
    },
    83: { # Screen Overlay
        1: ("overlay", enums.enumScreenOverlay), # 0 = Black Screen, 1 = Image Card Overlay (must call an "Image Card" opcode before using this!), 2 = Dark Hazy
        2: ("overlay_status", enums.enumBool3),
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    84: {  # RESET_SCENE_SYSTEMS
        # no parameters used
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    85: { # Set Dialogue Properties / Channel Mask Override
        # Dual-layer functionality

        # 1. Audio layer: Channel Mask Override - assigns priority/mask to a character's audio channel slot
        # It uses the same parameters:
        # 1: ("character", enumCharacter),
        # 2: ("mask_value", None),            # Custom mask (0-3 observed); ignored if p3==0
        # 3: ("apply_custom_mask", enumBool), # True: use mask_value, False: force override
        # 4: ("invert_flag", enumBool),       # Inverts channel routing behavior

        # 2. Gameplayer layer is used below:
        1: ("character", enums.enumCharacter),
        2: ("name_override", enums.enumDialogueNameOverride), # only works when param3=1 (enabled)
        3: ("enable_changes", enums.enumBool2),               # must be 1 for param2 and param4 to work
        4: ("hide_portrait", enums.enumBool2),                # only works when param3=1 (enabled)
        **{i: (f"param{i}", None) for i in range(5, 12)},
    },
    86: {  # Clear Frame State
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    87: { # Camera Movement
        1: ("camera_angle", None),
        2: ("panning", enums.enumCameraPan),
        3: ("unknown", None), # usually -1, but can also be 0-2 - probably similar to opcode 73's param4 (sentinel?)
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    88: { # Camera Pan
        1: ("preset_index_A", enums.enumPanPreset88),   # camera start position, -1 = use current
        2: ("preset_index_B", enums.enumPanPreset88),   # camera end position, -1 = use current
        3: ("duration_frames", None),             # in frames; 0 = instant)
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    89: { # Dialogue 1-Choice Menu
        1: ("choice_var_id", None),     # Gating ID for dialogue advancement state machine
        2: ("text_id_slot1", None),     # 1 allocated text index ID
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    90: {  # Dialogue Page Separator
        # Marks boundary between dialogue pages; triggers page-advance check in TalkEvent_Tick.
        # Note: if param1 is -1, the separator still stalls (unconditional active=0 at the end) but skips all the state changes.
        # This is probably a no-op placeholder separator used to create a stall point without actually registering a new page.
        1: ("page_id", None),  # unique page separator identity
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    91: { # All Look At Character
        # Also recomputes 3D pan coefficients for all 11 active voice channels relative to target.
        # This is the audio side-effect triggered when cutscene focus shifts to a character.
        1: ("target_char", enums.enumCharacter),           # directly indexes camera movement table entry
        2: ("speaker_pan_mode", enums.enumSpeakerPanMode), # 0=raw angle, 1=stereo, 2=surround (always 0 in practice)
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    92: {  # STUB_ADVANCE
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    93: {  # Set Position Yaw Override
        # Can be used to deviate the characters' facing directions from their layout preset defaults,
        # per cutscene position, without needing to redefine the entire layout table
        1: ("slot_index", None),    # position slot (0-11, wraps via % 12 on abs_pos_idx)
        2: ("yaw_degrees", None),   # facing angle in integer degrees; -360 to clear/reset
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    94: { # Character Look At
        # Makes src_char turn to face dest_char. The body and head orient toward dest_char's position,
        # and the spatial audio pan is updated to match.
        1: ("src_char", enums.enumCharacter),   # character doing the looking (looker)
        2: ("dest_char", enums.enumCharacter),  # character being looked at (target)
        3: ("mode", enums.enumCharLookAtMode),  # 0 = track dest_char's head bone
                                                # 1 (default) = track dest_char's body center
                                                # 2 = face src_char's preset yaw direction
                                                # -1 = instant orient + head turn
        4: ("turn_duration", None),      # body turn time in frames - used as minimum duration; actual time scales with angular distance; head turn speed = half this value
        **{i: (f"param{i}", None) for i in range(5, 12)},
    },
    95: { # Give Item To Character / Assign Ambient Sound Slot
        # 1. Audio layer (Assign Ambient Sound Slot):
        #  param1: sound_id - valid in any game sound bank range: 10–509, 600–649, 1000–1199, 1400–1622, 4000–4037, 5000–5002, 6000–6079, 7000–7059
        #  param2: tag_value - stored to AudioScene+0x7FB0 as a global ambient tag; -1 (0xFFFFFFFF) is normalised to 0; likely a priority/category marker
        # 2. Gameplay layer (Give Item To Character):
        #  param1: item_id - add +10
        #  param2: character - conditional grant + optional character binding?
        # The gameplay layer is what's used here, as that's the primary use. The other could be an internal engine setting that goes along with it.
        1: ("item_id", enums.enumScriptItem),         # Note: the actual item_id is "item_id + 10" - the enum already accounts for this
        2: ("character", enums.enumCharacter),        # Note: -1 (0xFFFFFFFF) = give it to the party, and not to a specific character
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    96: { # Emote Effect
        1: ("character", enums.enumCharacter),
        2: ("emote_effect", enums.enumEmoteEffect),
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    97: {  # Wait For Body Turn
        # This stops the batch execution and waits passively for the body turn controller to finish.
        # The more "advanced version" is at opcode 134
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    98: { # Character Eyes
        1: ("character", enums.enumCharacter),
        2: ("eyes", enums.enumEyes), # 0=Closed, 1=Open, 2=Suppress_AutoFade (suppress the voice auto-fade timer kill only), 3+=Clear_Suppress (re-enable the auto-fade timer only)
                                     # Value 2 and 3+ doesn't do anything with the eyes, they are only used to manipulate the voice auto-fade timer
                                      # 2 is used to stop the auto-fade timer (~3–7 seconds); used to stop the voice stream dying.
                                      # It's for silent reactions, while someone else speaks - to keep the Character Expression mode's (103) audio continue uninterrupted.
                                      # This was only used once in the "6965" EV script (Hubert-Bernadetta C support)
        3: ("frames_for_motion", None),  # animation duration in frames (only if eyes=0 or eyes=1)
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    99: { # Route Change
        1: ("route_id", enums.enumRoute),
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    100: { # Camera Move Direct
        # This command explicitly clears the focal character.
        # It's used for establishing shots or transitional cuts where no character should be tracked for spatial audio (unlike 87/88).
        1: ("camera_pos", None),
        2: ("panning", enums.enumCameraPan),
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    101: { # Camera Layout Transition
        # Transitions the camera/listener position to focus on a character using a layout preset.
        1: ("layout_preset", None), # 0-13
        2: ("character_id", enums.enumCharacter),
        3: ("speaker_pan_mode", enums.enumCameraPanMode101),
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    102: {  # Set Voice Blend Mode
        # Sets the scheduled voice action type for a character's slot.
        # Sequencer advances (seq_advance=1) but sets pause flag (0x67A3=1).
        1: ("character", enums.enumCharacter),
        2: ("mode", None),          # voice scheduling action type (0–13 valid)
                                    # 0–8 seen in scripts; 9–13 exist but are probably internal
                                    # If higher than 13, it's normalised back to current pending ID or 0
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    103: { # Character Expression Mode
        1: ("character", enums.enumCharacter),
        2: ("mode", enums.enumCharExpressionMode), # expression state (0-6); 0xFFFFFFFF is explicitly rejected
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    104: {  # Set Head And Body Orientation
        # This sets both head yaw and pitch simultaneously in one command
        # Opcode 24 sets pitch only and opcode 69 sets yaw only
        1: ("character", enums.enumCharacter),
        2: ("yaw_preset", None),                      # (float, radians)
        3: ("mode", enums.enumTurnOrient104),         # gameplay-layer only (0-6), -1 = stop looking at anything, return to neutral
        4: ("pitch_preset_and_frame_duration", None), # dual-use: param4=0 means "instant snap to neutral pitch", param4=30 means "pitch to −table[30] over 30 frames", etc.
        **{i: (f"param{i}", None) for i in range(5, 12)},
    },
    105: { # Image Card
        1: ("image_card", enums.enumCard),
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    106: {  # Update Mouth Animation
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    107: {  # Enqueue Animation Action
        1: ("action_type", enums.enumEnqueueAnimType),  # Body-action table; 0-15, full table of side effects per type
                                                        # Types 6/8 also dispatch a silent voice; types 10/11/12 set blend-end flags
                                                        # Scripts only use 0-9
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    108: {  # Cancel Active AnimSeq Slots
        # Cancels active non-blend-end slots (broad clear including body-turn actions)
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    109: {  # Set Scene Color RGB
        # Pure scene color set with RGB floats
        # The scale is 0–100, e.g. 50 = 0.5
        # Negative values will become 0.0
        # E.g. black would be 0,0,0 (for each params)
        1: ("red", None),
        2: ("green", None),
        3: ("blue", None),
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    110: {  # Cancel Emote Effects
        # Cancels character-emote slots specifically (char_id >= 0 filter)
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    111: {  # STUB_ADVANCE
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    112: {  # Set Ambient Layer Direction
        1: ("angle_degrees", None), # rotation angle; converts to (90−θ)° then stores as a (sin, 0, cos, 0) XZ unit vector
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    113: {  # Load Dialogue Line
        # Stalls sequencer until audio loads
        1: ("character", enums.enumCharacter),
        2: ("text_line_idx", None),  # index into speech table (capped to < 400). Points to the displayed subtitle text string.
        3: ("audio_event_id", None), # pre-resolved audio asset ID (from DAT_7100cee6e0 event table); 0xFFFFFFFF = use already-loaded stream
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    114: {  # Set BGM Variant B
        1: ("enable", enums.enumBool),       # 1: True, 0: False
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    115: {  # Refresh Character Audio Position
        # Looks up the character's current layout position slot (from TrackState+0xE4..+0xF8, the char_layout_pos array set by opcode 0x1D),
        # reads position XZY + yaw from the layout table (+yaw override), calls TrackSlot_Allocator to re-assign their audio slot at that position,
        # resets voice state, sets slot mode=0x40. Sets active=1 and pause=1.
        1: ("character", enums.enumCharacter),
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    116: {  # Set Character Slot Idle
        # Non-cutscene: sets slot mode=0x41 (idle), clears Y-motion gate, clears flag.
        # Cutscene mode: starts/advances stream, clears voice state, sets gate=1 (full deactivation).
        # Basically use this to idle the slot.
        1: ("character", enums.enumCharacter),
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    117: {  # STUB_ADVANCE
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    118: {  # Set Crossfade Slot Mode
        # Routes spatial audio through the KtslPlayer bank index rather than a specific character's pending track ID.
        # Enables two-bank crossfade for multi-speaker dialogue transitions where both banks (0 and 1) are active simultaneously.
        # So the spatial audio system routes by bank rather than by character.
        1: ("enable", enums.enumBool),
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    119: {  # SELECT_CHANNEL
        # Channel selector (control marker) - marks start of a channel block; matched by channel ID in param1
        1: ("channel_id", None),
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    120: {  # END_OF_STEP
        # End of Step (control marker) - terminates execution for this PC tick, loops back next frame
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    121: {  # Set Character Pair
        # Declares a pairing relationship: char_a is associated with char_b for spatial audio.
        1: ("char_a", enums.enumCharacter), # primary character
        2: ("char_b", enums.enumCharacter), # paired character
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    122: {  # Set Camera Direction Override
        # Forces the camera facing direction. Never cleared automatically.
        # If it's not -1, it skips the entire character-position vote and uses the given direction directly.
        # This lets scripts persistently lock the camera to a specific side across multiple dialogue pages.
        1: ("direction", enums.enumCameraDirection),
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    123: {  # Suppress Next Audio Start
        # The next dialogue voice transition (opcode 33/34/89) will go through the suppress path:
        # camera/tracking state is cleaned up exactly as after a normal transition, but no audio fires. The currently-playing audio is untouched.
        # Use case - Silent dialogue transition: reset the spatial audio scene state (camera counters, listener tracking) without starting a new voice line.
        # Scripts use this to resync scene state for a subsequent dialogue block without an audible gap.
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    124: {  # Condition Slot RNG Init
        # Rolls a random integer and stores it into a slot of the condition slot array at TrackState+0x154.
        # This array is read by opcode 35 and by TrackHandler_DispatchVoice (opcode 81 gate path).
        # 1. Opcode 35 (conditional statement):
        #  A. Type 3 (Condition_Slot_Nonzero): condition_slots[index] > 0
        #  B. Type 9 (Condition_Slot_Exact_Match): condition_slots[index] == expected_value
        # 2. Also used by TrackHandler_DispatchVoice (opcode 81 voice gate):
        #  if condition_slots[cmd[7]] >= 0: suppress voice
        1: ("slot_index", None),      # Index into TrackState+0x154 array (stride 4)
        2: ("max_range", None),       # Upper bound for RNG (exclusive)
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    125: {  # Conditional Branch by Character ID | BRANCH IF ACTIVE_CHAR == MATCH_CHAR
        # Used for checking "who won / who is selected" in the White Heron Cup.
        # It's used whenever a scene needs to play different dialogue or camera angles depending on which specific named character holds a role determined by gameplay
        # (winner, route-selected student, etc.).
        1: ("match_char", enums.enumCharacter), # check for character ID
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    126: {  # Conditional Branch by House Lord Index | BRANCH IF ACTIVE_CHAR == HOUSE_LORD_N
        # Used when you need to branch by faction/lord (Edelgard's side, Dimitri's side, Claude's side) without caring about the specific character ID.
        1: ("house_lord_id", enums.enumCharHouseLords), # check for house lord ID
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    127: {  # Conditional Battle Completion
        # This is a scope-conditional wrapper around the exact same call that Condition_EvaluateAndSkip type 2 uses.
        # Battle completion isn't stored in a separate battle-tracking structure, it's in the same flat item-flag table as everything else in the game state.
        # Out-of-range handling: if completion_status == 0 (Completed) -> FAIL; if completion_status == 1 (Not_Completed) -> PASS. Treats nonexistent maps as always-incomplete.
        1: ("map_id", enums.enumMapID),
        2: ("completion_status", enums.enumCompleted),
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    128: {  # Conditional Event Flag Check
        # Used to check what was set with opcode 46
        1: ("flag_id", enums.enumEventFlags),
        2: ("expected_value", enums.enumConditionalEventType),
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    129: {  # Set Subtitle And Portrait Mode
        # Simultaneously enables or disables both the subtitle text display subsystem and the portrait/image-card rendering for the current voice channel.
        # 1. Controls whether this channel's subtitle text box is output-enabled.
        # 2. Controls whether the portrait / image-card rendering is active for the channel.
        # This controls whether the channel's display subsystem (subtitle + portrait) is active all.
        #  Scripts use this to tear down the display before a scene transition or to gate complex dialogue choice sequences.
        1: ("mode", enums.enumBool4),
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    130: {  # Fancy Dialogue Choice Menu
        # Full Fancy Dialogue Choice Menu (multi-option branching presentation)
        # The audio layer's only job here is arming the VoiceAllocator to treat the subsequently committed voice slots as "fancy choice" slots
        # which changes VoiceAllocator+0xBD from 0 to 2 and activates VoiceChannel+0x1900 per-slot markers that downstream scheduling
        # reads to know these are branching-choice voice lines, not linear ones.
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    131: {  # Set Active Voice-Channel Roster
        # Maintains the TrackHandler's 11-slot active-channel registry at TrackState+0x13C..+0x150.
        # Tracks which character voice channel IDs are currently registered in the active scene.
        # Add when a character enters, remove when a character exits.
        # Other opcodes that iterate channel assignments read this ring to validate/enumerate active channels.
        # If all 11 slots are occupied: skip without error.
        1: ("mode", enums.enumBool5), # 0 = remove, nonzero = add
        2: ("sound_id1", enums.enumSoundID131), # -1 = skip
        3: ("sound_id2", enums.enumSoundID131), # -1 = skip
        4: ("sound_id3", enums.enumSoundID131), # -1 = skip
        5: ("sound_id4", enums.enumSoundID131), # -1 = skip
        **{i: (f"param{i}", None) for i in range(6, 12)},
    },
    132: {  # Display Item Reward
        1: ("item_id", enums.enumScriptItem), # pending_item_reward_id, -1 = nothing pending
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    133: {  # Preserve Music Flag
        # Used to sustain music (BGM) past the cutscene
        # Useful in scenarios where the voice system shuts down before the BGM cleanup runs
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    134: {  # BodyTurn + CharActor Anim Coordinated Wait
        # Compared to the simpler opcode 97, this actively drives the character animation system through the turn, then waits for a secondary completion signal.
        # This has two distinct stall modes:
        # Phase 1: turn in progress / no controller
        # Phase 2: turn just completed / guards set
        1: ("duration_ticks", None), # Animation wait duration - written as float
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    135: {  # Enter Animation Queue | QUEUE_MODE: Command Queue Mode - enables command queuing/buffering mode (for timed animation sync)
        # While active, certain subsequent opcodes buffer into a ring (capacity 40 x 0x30 bytes) instead of executing immediately.

        # The only opcodes that work (get added) for the queue buffer are: 11 (Animation), 17 (SFX), 23 (Body Motion), 24 (Head Motion X),
        # 66 (Play SFX From Table), 67 (Set Body Facing Angle), 69 (Head Motion Y), 91 (All Look At Character), 94 (Character Look At),
        # 96 (Emote Effect), 98 (Character Eyes), 102 (Set Voice Blend Mode), 103 (Character Expression Mode), 104 (Set Head And Body Orientation)

        # These are mostly animation or in-place character movement/body changes, with SFX support.

        # This buffer can be used to trigger those specific commands simultaneously up to 40 commands.
        # So if there are 41 commands or more that would also need he queue, the 41th and beyond are not affected
        # and would require another opcode 135 call in such intervals (after the 40th command)

        # Any other opcode from the aforementioned will not be placed in the buffer and does execute normally, but only if they match the following opcodes...
        # Only these opcodes can execute: 3 (Dialogue Box), 9 (Abort Queue Window), 79 (Character Check), 81 (Dialogue Box Gated), 138 (Commit Animation Queue)
        # Opcode 9 is for an emergency abort, and one should use opcode 138 instead to finish the queue properly.
        # Anything besides these get silently dropped (zero effect) while the queue mode is on.

        # So it's primarily used for timing animation/in-place character movements and SFX with dialogue entries and also a character status check opcode.

        1: ("timing_in_frames", None), # queue sync timing value in frames
                                       # 0 value here is a special case: the countdown gate requires > 0 to run, so a zero value means "never fire via countdown" 
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    136: {  # Screen Fade - Sets screen color overlay and fade timing only
        # Use with opcode 109 to change colors (RGB), then use this
        # If opcode 109 is never called, the fade-on uses whatever color is already present in there (most likely just pure black)
        1: ("mode", enums.enumFade),    # 0=fade off/reset, 1=fade on
        2: ("duration_frames", None),   # fade duration (e.g., 300 = 5 seconds)
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    137: {  # Animation Action Activation Pending?
        # Related with opcodes 107/108
        # Finds an AnimSeq slot by action_id, sets/toggles bit 3 of its flags.
        # Sets needs_update=1 so the animation system processes the change this frame.
        1: ("action_id", None),                 # Scan AnimSeq 16-slot array for this ID at slot+0x1C
        2: ("mode", enums.enumAnimSeqFlagBit3), # 0 = SET bit 3 (flags |= 0x08); 1 = TOGGLE bit 3 (flags ^= 0x08)
                                                # Based on the parallel bit 3 on audio event tables, this is probably a dispatch gate or activation pending flag
                                                # This likely controls whether the animation resource is active vs held.
                                                # Set=arm/activate, Toggle=flip between active/suspended
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    138: {  # Commit Animation Queue | FLUSH_QUEUE
        # Fires all accumulated commands simultaneously.
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    139: {  # Scene Event (Reset Walk-In State)
        # Used for characters about to walk in - it zeroes the walk-in tracker fields and sets the "active/in-progress" flags,
        # so the movement system knows they're freshly entering and should be tracked.
        # This enables smooth walk-in animation when they arrive mid-scene.
        # Use case: probably for new characters that were not present in the scene before
        1: ("event_function", enums.enumSceneEvent),
        **{i: (f"char{i-1}", enums.enumCharacter) for i in range(2, 12)},
    },
    140: {  # Camera Position
        # Repositions the current camera to X,Y,Z
        1: ("pos_x", None),
        2: ("pos_y", None),
        3: ("pos_z", None),
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    141: {  # Ambient Layer Position
        # Paired with opcode 112, which together define the full spatial origin and orientation of the ambient audio layer source
        # Only known script usage: pos_x=0, pos_y=0, pos_z=300
        # Which places the ambient source at (0.0f, 150.0f, 300.0f, 1.0f)
        # The Y=150.0f comes purely from the hardcoded bias (150.0f)
        1: ("pos_x", None), # engine stores as float; pos_y gets +150.0 offset added at runtime
        2: ("pos_y", None), # script value is scene-space Y; audio system origin is Y+150
        3: ("pos_z", None), # w=1.0 constant appended by engine (homogeneous coord)
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    142: {  # Character Walk-In Animation A
        # Signals the gameplay layer to play a walk-in animation for a character entering the scene,
        # and records the walk-in animation ID + scene bone slot into the AnimChannel display cluster.
        # Identical audio-layer bodies. Gameplay-layer event type could differ between 142 and 143.
        # One could be hardcoded "Right", the other "Left" direction or similar.
        1: ("walk_in_anim_id", enums.enumAnimation), # Walk-in animation preset (uint). Must be < 195. If >= 195: entire body is skipped
                                                     # Selects which entry animation the character plays.
        2: ("bone_slot_index", None),                # Scene bone/attachment slot the character enters into (signed int).
                                                     # Specifies the target position slot in the scene's character rig.
                                                     # Assumption: this is the slot in the scene's character attachment rig where the character anchors once they arrive.
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    143: {  # Character Walk-In Animation B
        # Signals the gameplay layer to play a walk-in animation for a character entering the scene,
        # and records the walk-in animation ID + scene bone slot into the display cluster.
        # Identical audio-layer bodies. Gameplay-layer event type could differ between 142 and 143.
        # One could be hardcoded "Right", the other "Left" direction or similar.
        1: ("walk_in_anim_id", enums.enumAnimation), # Walk-in animation preset (uint). Must be < 195. If >= 195: entire body is skipped
                                                     # Selects which entry animation the character plays.
        2: ("bone_slot_index", None),                # Scene bone/attachment slot the character enters into (signed int).
                                                     # Specifies the target position slot in the scene's character rig.
                                                     # Assumption: this is the slot in the scene's character attachment rig where the character anchors once they arrive.
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    144: {  # Voice 3D Pan - sets spatial audio position for a character's voice stream
        1: ("character", enums.enumCharacter),
        2: ("pos_y", None),            # Y position in 3D audio field
        3: ("pos_x", None),            # X position in 3D audio field
        4: ("pos_z", None),            # Z depth (observed: -25, -100; negative = forward/down)
        **{i: (f"param{i}", None) for i in range(5, 12)},
    },
    145: {  # Camera Flip
        # Dialogue camera flip: the ~180° camera reversal that swings the viewpoint to face the other character when they begin speaking.
        # This schedules the camera to switch from the default angle preset to the "alternate" (flipped) preset.
        # Note: this isn't purely a camera operation: it's the moment the scene considers a character-switch to have landed, resetting the dialogue UI to match.
        # It invalidates the currently-tracked active speaker ID, forcing the portrait system to reselect based on whoever is now facing the camera.
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    146: {  # Change Cube Label To
        # Assembles location, time, and month strings,
        # then renders them via TextTable templates (0x6DE/0x6DF).
        1: ("location", enums.enumLocation),
        2: ("timeOfDay", enums.enumTimeOfDay),
        3: ("month", enums.enumMonth),  # -1 (0xFFFFFFFF) = skip month line entirely
        **{i: (f"param{i}", None) for i in range(4, 12)},
    },
    147: {  # Load Item
        # Dual-purpose function:
        # 1. NOP (audio layer does nothing)
        # 2. Load Item ID (and then add the same item ID with opcode 95)
        1: ("item_id", enums.enumScriptItem),  # Note: the actual item_id is "item_id + 10" - the enum already accounts for this
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    148: {  # Anim Audio Continuity
        # Typical use: call opcode 148 with action_type=N before opcode 107 with the same N
        # to re-enqueue the animation without restarting its sustained audio (types 6/8 especially).
        1: ("action_type", None),  # pre-seeds AnimSeq+0x418; when the next CharAnim_EnqueueAction fires with this same type, the audio fade-out and restart are suppressed
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    149: {  # Set Ambient Volume
        1: ("volume", None),          # int: 0-100 (divided by 100.0, same as scene color), e.g. 50 = 0.5
        2: ("duration_frames", None), # int: multiplied by 1/60; seconds for fade
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },
    150: {  # Divine Pulse Increment
        # Increases the Divine Pulse charges by 1 (until maximum allowed value depending on difficulty). No parameters.
        # Executed at the end of the cutscene.
        **{i: (f"param{i}", None) for i in range(1, 12)},
    },
    153: {  # Auto-Advance Delay
        # Sets the dialogue auto-advance frame threshold.
        # Only active if the player has the auto-advance mode on, otherwise this does nothing.
        # Used for controlling the pacing for auto-mode players during scripted dramatic sequences.
        # The only known example is in 6415, which uses an artificially high frame_count of 1800
        # Use case: even if the player has auto-advance mode enabled, the engine won't auto-advance that (dialogue) page until
        # after the 1860-frame pause has run its course (in that script).
        # Then it's set back to 0, which means to restore fast auto-advance for whatever comes next (don't keep it that high to annoy the player).
        1: ("frame_count", None),   # int32 value
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
    154: {i: (f"param{i}", None) for i in range(1, 12)},  # Angry Dimitri
    155: {  # Store Channel A (Internal Registry) - NOT USED BY SCRIPTS (but included for completeness)
        # BINARY NOTE: Writes validated channel ID to TrackState+0x974, 
        # and p2 to TrackState+0x12F. Used by compiler/engine for 
        # BGM routing or crossfade target reservation. No immediate effect.
        1: ("channel_a_id", None),
        2: ("channel_a_aux", None),
        **{i: (f"param{i}", None) for i in range(3, 12)},
    },

    156: {  # Store Channel B (Internal Registry) - NOT USED BY SCRIPTS (but included for completeness)
        # BINARY NOTE: Writes validated channel ID to TrackState+0x97C. 
        # Pairs with 155 for dual-channel reservation/routing setup.
        1: ("channel_b_id", None),
        **{i: (f"param{i}", None) for i in range(2, 12)},
    },
}

######################################
### Event parameter counts
######################################

# Used for removing the unused fields
event_param_counts = {
     0:   3,
     1:  11,
     2:   0,
     3:   6,
     4:  11,
     5:  11,
     6:   3,
     7:   3,
     8:   0,
     9:   0,
    10:   5,
    11:   5,
    12:   0,
    13:   1,
    14:   0,
    15:   1,
    16:   1,
    17:   1,
    18:   1,
    20:   1,
    21:   0,
    22:   1,
    23:   3,
    24:   3,
    25:   3,
    26:   2,
    27:   3,
    28:  11,
    29:   2,
    30:   1,
    31:   3,
    32:   2,
    33:   3,
    34:   4,
    35:   3,
    36:   0,
    37:   0,
    38:   3,
    39:   0,
    40:   0,
    41:   0,
    42:   0,
    43:   3,
    45:   3,
    46:   2,
    47:   2,
    48:   0,
    49:   0,
    50:   0,
    51:   1,
    52:   1,
    53:   1,
    54:   4,
    55:   0,
    56:   0,
    57:   2,
    58:   0,
    59:   4,
    60:   1,
    61:   2,
    62:   0,
    63:   2,
    64:   4,
    65:   1,
    66:   2,
    67:   4,
    68:   0,
    69:   3,
    70:   0,
    71:   4,
    72:   0,
    73:   4,
    74:   0,
    75:   0,
    76:   0,
    77:   0,
    78:   8,
    79:  11,
    80:   5,
    81:   7,
    82:   5,
    83:   2,
    84:   0,
    85:   4,
    86:   0,
    87:   3,
    88:   3,
    89:   2,
    90:   1,
    91:   2,
    92:   0,
    93:   2,
    94:   4,
    95:   2,
    96:   2,
    97:   0,
    98:   3,
    99:   1,
    100:  2,
    101:  3,
    102:  2,
    103:  2,
    104:  4,
    105:  1,
    106:  0,
    107:  1,
    108:  0,
    109:  3,
    110:  0,
    111:  0,
    112:  1,
    113:  3,
    114:  1,
    115:  1,
    116:  1,
    117:  0,
    118:  1,
    119:  1,
    120:  0,
    121:  2,
    122:  1,
    123:  0,
    124:  2,
    125:  1,
    126:  1,
    127:  2,
    128:  2,
    129:  1,
    130:  0,
    131:  5,
    132:  1,
    133:  0,
    134:  1,
    135:  1,
    136:  2,
    137:  2,
    138:  0,
    139: 11,
    140:  3,
    141:  3,
    142:  2,
    143:  2,
    144:  4,
    145:  0,
    146:  3,
    147:  1,
    148:  1,
    149:  2,
    150:  0,
    153:  1,
    154:  0,
    155:  2,
    156:  1
}
