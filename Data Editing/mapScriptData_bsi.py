import json
import os
import re
import struct
import sys

# Constants
HEADER_SIZE = 56        # 14 x uint32
EVENT_HEADER_SIZE = 48  # 12 x uint32
BLOCK1_FIXED_SIZE = 16  # 4 x uint32 before CommandsAndArgs[]
BLOCK2_SIZE = 16        # 4 x uint32

# Format: Opcode: ("ShortName", ParamCount)
CONDITIONS = {
    0: ("DidScriptRun", 3), 10: ("CheckVariable", 4), 20: ("CheckFlag70", 3),
    30: ("StartOfMap", 1), 50: ("KillCheck", 4), 60: ("IsCharDead", 3),
    70: ("HP%Char", 4), 80: ("BAIDeathCheck", 3), 90: ("HP%BAI", 4),
    100: ("BAIonTile", 4), 110: ("UnitOutsideRect", 7), 120: ("CheckTeamSurvivors", 5),
    130: ("InteractedTerrain", 3), 140: ("DifficultyCheck", 3), 170: ("Start1stTurn", 1),
    180: ("StartPlayerPhase", 1), 190: ("StartEnemyPhase", 1), 200: ("UnitSelected", 2),
    210: ("MapState", 1), 220: ("TurnCount", 5), 230: ("IsAdjacentTo", 3),
    240: ("UnitInRange", 5), 250: ("MapRecruitedAvail", 2), 260: ("BAIinTeam", 3),
    280: ("TeamInRange", 5), 300: ("CharsBattling", 5), 310: ("TeamIntoSpace", 4),
    320: ("TeamOutsideRect", 7), 330: ("DuringCharBattle", 7), 340: ("RouteCheck", 3),
    350: ("DuringBAIBattle", 5), 360: ("AfterBAIBattle", 2), 370: ("BylethGenderCheck", 2),
    380: ("IsTileDoorBridge", 3), 390: ("CountUnitDefeated", 4), 400: ("EndTeamPhase", 2),
    410: ("StartTeamPhase", 2), 420: ("CharInRect", 7), 430: ("TeamHighestKill", 2),
    440: ("StartOfBattle", 1), 450: ("TeamsBattling", 5), 470: ("TeamBattleDefeat", 5),
    480: ("MapCompleted", 1), 490: ("ItemInvCheck", 4), 500: ("UnitStatusEffect", 3),
    510: ("MapGimmickActive", 2), 520: ("GameModeCheck", 3), 530: ("RecruitedUnavail", 2),
    540: ("AfterUnitAction", 1), 550: ("TalkConversation", 2), 560: ("UndergroundChamber", 1),
    570: ("RecruitedButDied", 2), 580: ("StaggeringBlowUsed", 1), 590: ("AshenWolvesGimmick", 3),
    1000: ("MonasteryTalkedTo", 3), 1010: ("QuestStatusCheck", 3), 1020: ("EventFlagCheck", 3),
    1030: ("QuestBattleCleared", 3), 1060: ("SupportRankCheck", 6), 1070: ("MiscItemCount", 3),
    1080: ("CheckGiftedQuestItem", 3), 1110: ("EventViewed", 2), 1120: ("DialogueChoice", 4),
    1130: ("MonasteryRecruitment", 4), 1140: ("NPCatCoord", 4), 1150: ("NPCinRect", 7),
    1160: ("DialogueSessionActive", 2), 1170: ("PlayerInMonasteryArea", 2), 1180: ("CalendarDay", 3),
    1190: ("CharRecruitedCheck", 4), 1200: ("BylethSupportPoints", 2), 1210: ("NG+DLCCheck", 3),
    1220: ("ChapterCheck", 3), 1230: ("TalkedToCharID", 2), 1240: ("MonasteryItemCheck", 3),
    1250: ("CharLevelCheck", 4), 1270: ("WhiteHeronCupSelect", 3), 1280: ("NormalExplorationMode", 2),
    1290: ("MonasteryState0x10", 2), 1310: ("NoExplorationAvail", 2), 1320: ("TutorialViewed", 2),
    1330: ("UpdateDLCCheck", 3), 1340: ("CinderedShadowsChap", 3), 1350: ("MonasterySunlight", 2),
    1360: ("InfluencerLevel", 3),
    270:  ("AlwaysFalse270", 3),  # always returns FALSE
    290:  ("AlwaysFalse290", 2),  # always returns FALSE
    1090: ("AlwaysFalse1090", 2), # always returns FALSE
    1300: ("AlwaysFalse1300", 3), # WorldState_IsMonastery() then returns FALSE
    99998: ("AND", 3),  # Recursive
    99999: ("OR", 3)    # Recursive
}

ACTIONS = {
    # Unknowns: 220 (Thales/Shambhala), 2570, 2580, 2590, 2600
    0: ("ShowTextS", 1), 15: ("DialogueTextV", 5), 20: ("PlayBGM", 2),
    30: ("BGMPlayStopTiming", 1), 40: ("InitVariable", 2), 50: ("IncrementVariable", 2),
    60: ("RandomizeVariable", 2), 70: ("SetFlag70", 2), 80: ("RunScript", 1),
    90: ("EndMission", 1), 130: ("SpawnUnitBAICoords", 7), 140: ("MoveBAI", 10),
    150: ("ReplaceBAI", 9), 160: ("RemoveBAIFromMap", 5), 170: ("RemoveTeamFromMap", 6),
    180: ("SpawnRelated", 1), 200: ("ApplySothisFusion", 2), 220: ("Unknown220", 2),
    240: ("GiveBAIItem", 2), 250: ("BAIUseItem", 2), 270: ("TerrainToggle", 1),
    320: ("GrayOutBAISlot", 1), 330: ("MoveCameraToBAI", 4), 340: ("MoveCameraToCoords", 5),
    370: ("UnitToAI2", 7), 380: ("UnitToRectAI", 7), 400: ("HighlightTiles", 7),
    430: ("PlayMovieEvent", 2), 440: ("SetMovementFlag", 2), 450: ("ReviveUnit", 4),
    460: ("ApplyStatusBAI", 3), 470: ("ApplyStatusTeam", 8), 480: ("RecruitCharID", 1),
    530: ("UnitBattalionStatus", 2), 540: ("ChangeUnitStatus", 3), 550: ("ShowTutorial550", 1), 560: ("SetVarToTurnCount", 1),
    570: ("OpenDoor", 2), 580: ("RectAIThief", 7), 590: ("SetupWarpTilePair", 4),
    600: ("SetUnitPosition", 4), 610: ("KeepUnitOnMapDefeated", 3), 620: ("SpawnSpooky", 5),
    630: ("ChangeRotation", 2), 640: ("FadeToBlack", 1), 650: ("ShortPause", 0),
    660: ("PersuadeOrKill", 3), 670: ("TutorialMultiOption", 2), 680: ("SpareOrKill", 2),
    690: ("MoveUnitToAI", 7), 700: ("GrantBattalion", 1), 710: ("UpdateMapConditions", 2),
    720: ("GrantItemQty", 2), 730: ("RemoveBAIInv", 1), 740: ("SetDefeatText", 2),
    750: ("EnemyNotDieIfDefeated", 1), 760: ("AudioOnOff", 2), 770: ("Internal770", 1),
    780: ("PlayCutscene", 1), 790: ("UpdateBothCondLabels", 2), 800: ("StopMusic", 0),
    810: ("PlayBGMBAIBattles", 3), 820: ("RectAI820", 7), 830: ("GrantBAIDroppable", 2),
    840: ("ChaliceBlast", 6), 850: ("MapShake", 3), 860: ("FadeToWhite", 1),
    2000: ("SetDialogueEntry", 2), 2010: ("SetMonasteryDialogue", 2), 2030: ("SpawnMonasteryBAI", 1),
    2040: ("RemoveMonasteryBAI", 1), 2050: ("PlayCutsceneMonastery", 1), 2060: ("ViewMovieSetVoicePos", 1),
    2070: ("SetEventFlag", 2), 2100: ("SetQuestStatus", 2), 2120: ("ShowTutorial2120", 1),
    2160: ("SetMonasteryCamera", 8), 2170: ("MonasteryCameraZoom", 1), 2180: ("MoveMonasteryBAI", 4),
    2190: ("GiveSupportPoints", 4), 2210: ("SetNPCB4Value", 2), 2220: ("NOP2220", 1),
    2230: ("NOP2230", 1), 2240: ("NOP2240", 1), 2250: ("NOP2250", 1), 2270: ("NOP2270", 1),    
    2280: ("NOP2280", 1), 2260: ("LostItemNotif", 3),
    2300: ("CreateTalkingGroup", 4), 2340: ("SetSceneIntroCameraTween", 10), 2350: ("AddMoney", 1),
    2360: ("MonasteryFadeToBlack", 1), 2370: ("BylethDialogueChoices", 10), 2420: ("MonasteryDoorState", 2),
    2430: ("ShowVmesMonastery", 1), 2440: ("ShowChoiceDialogue", 1), 2450: ("LoadMonasteryScript", 1),
    2460: ("InstantlyExplore", 1), 2470: ("SkipToChapterMap", 0), 2480: ("EnableMonasteryRecruit", 5),
    2490: ("SetExplorationPoints", 1), 2500: ("SetupAuxBattleQuest", 2), 2510: ("MonasteryLockArea", 2),
    2520: ("MonasteryGrantItem", 3), 2530: ("MonasteryRemoveItem", 3), 2540: ("MonasteryDialogueRel", 1),
    2550: ("FlagBernadetta", 2), 2560: ("MonasteryItemSpots", 2), 2570: ("Unknown2570", 3),
    2580: ("Unknown2580", 2), 2590: ("Unknown2590", 2), 2600: ("Unknown2600", 0),
    2610: ("SetMonasteryDialogueChoice", 9), 2620: ("MonasteryCharRel", 1), 2640: ("WhiteHeronCupSelect", 2),
    2650: ("SetMonasteryToDoMsg", 2), 2660: ("RemoveMonasteryToDoMsg", 2), 2680: ("SetNPCD1", 2),
    2690: ("SetBubbleMessage", 2), 2700: ("SetParalogueAvail", 2), 2710: ("SetEdelgardSeminar", 2),
    2720: ("SetNPCD3bit3", 2), 2730: ("SetMonasterySpot", 2), 2740: ("SetQuestIndicator", 2),
    2750: ("HideInMiniMap", 2), 2760: ("EnableEndExploration", 1), 2770: ("MonasteryLocationAvailability", 2),
    2790: ("GrantLordsFinalClass", 1), 2800: ("EnableFastTravel", 1), 2810: ("ShowEndingCard", 1), 2820: ("SetVoiceCamDir", 4),
    2830: ("ShowEndingCard1411", 2), 2840: ("QuestIndicatorOnChar", 2), 2850: ("SetMonasterySpotActive", 2),
    2860: ("PlaceCharInAbyss", 4), 2870: ("MonasteryBAICS", 3)
}


def parse_condition(data, offset):
    opcode = data[offset]
    name, param_count = CONDITIONS.get(opcode, (f"UnknownCond_{opcode}", 0))
    params = data[offset+1 : offset+1+param_count]

    if opcode in (99998, 99999):
        child_count = params[1]
        children = []
        cur_offset = offset + 1 + param_count
        for _ in range(child_count):
            child, cur_offset = parse_condition(data, cur_offset)
            children.append(child)
        return {
            "Condition": name,
            "Opcode": opcode,
            "Params": params,
            "Children": children
        }, cur_offset
    else:
        return {
            "Condition": name,
            "Opcode": opcode,
            "Params": params
        }, offset + 1 + param_count

def parse_actions_block(data):
    actions = []
    offset = 0
    while offset < len(data):
        opcode = data[offset]
        name, param_count = ACTIONS.get(opcode, (f"UnknownAct_{opcode}", 0))
        params = data[offset+1 : offset+1+param_count]
        actions.append({
            "Action": name,
            "Opcode": opcode,
            "Params": params
        })
        offset += 1 + param_count
    return actions

def flatten_conditions(conditions):
    data = []
    for cond in conditions:
        data.append(cond["Opcode"])
        data.extend(cond["Params"])
        if cond["Opcode"] in (99998, 99999):
            data.extend(flatten_conditions(cond["Children"]))
    return data

def flatten_actions(actions):
    data = []
    for act in actions:
        data.append(act["Opcode"])
        data.extend(act["Params"])
    return data


def parse_bsi_file(filename):
    with open(filename, "rb") as f:
        data = f.read()

    result = {"OriginalFileSize": len(data)}

    h = struct.unpack_from("<14I", data, 0)
    start_of_events = h[8]

    # Robust calculation of event count in case header NumOfEvents is wrong
    num_events = (start_of_events - HEADER_SIZE) // 4
    if num_events != h[2]:
        print(f"Warning: Header NumOfEvents ({h[2]}) != PTR Table size ({num_events}). Using {num_events}.")

    result["Header"] = {
        "MagicNumber": h[0],
        "Unk1": h[1],
        "NumOfEvents": num_events,
        "Unk3": h[3],
        "Unk4": h[4],
        "Unk5": h[5],
        "Unk6": h[6],
        "Unk7": h[7],
    }

    ptr_table = []
    for i in range(num_events):
        off = struct.unpack_from("<I", data, HEADER_SIZE + i * 4)[0]
        ptr_table.append(off)

    events = []
    for i in range(num_events):
        eo = ptr_table[i]
        eh = struct.unpack_from("<12I", data, eo)

        p1 = eh[6]
        p2 = eh[7]
        p3 = eh[9]
        eob = eh[11]

        # Block1 (EventConditional)
        b2 = struct.unpack_from("<4I", data, p2)
        ec_name, _ = CONDITIONS.get(b2[0], (f"UnknownCond_{b2[0]}", 0))
        event_conditional = {
            "Condition": ec_name,
            "Opcode": b2[0],
            "Params": [b2[1], b2[2], b2[3]]
        }

        # Block2 (Conditions)
        b1 = struct.unpack_from("<4I", data, p1)
        cmd_count = b1[3]
        raw_conds = list(struct.unpack_from(f"<{cmd_count}I", data, p1 + BLOCK1_FIXED_SIZE)) if cmd_count > 0 else []

        cond_count = b1[2]
        conditions = []
        cur_offset = 0
        for _ in range(cond_count):
            cond, cur_offset = parse_condition(raw_conds, cur_offset)
            conditions.append(cond)

        block1 = {
            "ConditionType": b1[0],
            "Unk1": b1[1],
            "ConditionalCommandArgCount": cond_count,
            "Conditions": conditions
        }

        # Block3 (Actions)
        actions = []
        if eob > p3:
            act_count = (eob - p3) // 4
            raw_acts = list(struct.unpack_from(f"<{act_count}I", data, p3))
            actions = parse_actions_block(raw_acts)

        events.append({
            "EventNum": eh[0],
            "Unk1": eh[1],
            "TriggerParams": [eh[2], eh[3], eh[4], eh[5]],
            "EntryCount": eh[8],
            "Unk11": eh[10],
            "EventConditional": event_conditional,
            "ConditionsBlock": block1,
            "Actions": actions
        })

    result["Events"] = events
    return result


def repack_to_bsi(json_file, output_file=None):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    header = data["Header"]
    events = data["Events"]
    num_events = len(events)

    events_start = HEADER_SIZE + num_events * 4

    event_offsets = []
    pointer1_offsets = []
    pointer2_offsets = []
    pointer3_offsets = []
    end_of_blocks = []

    cur = events_start
    for ev in events:
        event_offsets.append(cur)
        p1 = cur + EVENT_HEADER_SIZE
        pointer1_offsets.append(p1)

        # Flatten conditions to calculate size
        conditions = flatten_conditions(ev["ConditionsBlock"]["Conditions"])
        cmd_count = len(conditions)
        p2 = p1 + BLOCK1_FIXED_SIZE + cmd_count * 4
        pointer2_offsets.append(p2)

        p3 = p2 + BLOCK2_SIZE
        pointer3_offsets.append(p3)

        # Flatten actions to calculate size
        actions = flatten_actions(ev["Actions"])
        eob = p3 + len(actions) * 4
        end_of_blocks.append(eob)

        cur = eob

    total_size = cur
    buf = bytearray(total_size)

    struct.pack_into(
        "<14I", buf, 0,
        header["MagicNumber"],
        header["Unk1"],
        num_events,
        header["Unk3"],
        header["Unk4"],
        header["Unk5"],
        header["Unk6"],
        header["Unk7"],
        events_start,
        total_size, total_size, total_size, total_size, total_size,
    )

    for i in range(num_events):
        struct.pack_into("<I", buf, HEADER_SIZE + i * 4, event_offsets[i])

    for i, ev in enumerate(events):
        eo = event_offsets[i]
        p1 = pointer1_offsets[i]
        p2 = pointer2_offsets[i]
        p3 = pointer3_offsets[i]
        eob = end_of_blocks[i]

        tp = ev["TriggerParams"]
        struct.pack_into(
            "<12I", buf, eo,
            ev["EventNum"],
            ev["Unk1"],
            tp[0], tp[1], tp[2], tp[3],
            p1, p2,
            ev["EntryCount"],
            p3,
            ev["Unk11"],
            eob,
        )

        b1 = ev["ConditionsBlock"]
        conditions = flatten_conditions(b1["Conditions"])
        struct.pack_into(
            "<4I", buf, p1,
            b1["ConditionType"],
            b1["Unk1"],
            b1["ConditionalCommandArgCount"],
            len(conditions),
        )
        if conditions:
            struct.pack_into(f"<{len(conditions)}I", buf, p1 + BLOCK1_FIXED_SIZE, *conditions)

        ec = ev["EventConditional"]
        struct.pack_into(
            "<4I", buf, p2,
            ec["Opcode"],
            ec["Params"][0], ec["Params"][1], ec["Params"][2],
        )

        actions = flatten_actions(ev["Actions"])
        if actions:
            struct.pack_into(f"<{len(actions)}I", buf, p3, *actions)

    if not output_file:
        output_file = os.path.splitext(json_file)[0] + "_repacked.bsi"

    with open(output_file, "wb") as f:
        f.write(buf)

    print(f"Repacked: {output_file} ({total_size} bytes)")


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python mapScriptData_bsi.py dump <input.bsi>")
        print("  python mapScriptData_bsi.py repack <input.json>")
        return

    mode = sys.argv[1].lower()
    input_file = sys.argv[2]

    if mode == "dump":
        parsed = parse_bsi_file(input_file)
        out = os.path.splitext(input_file)[0] + ".json"

        # Create JSON string with indent=4
        json_str = json.dumps(parsed, indent=4)

        # Post-process to flatten arrays containing only integers
        def compact_int_arrays(match):
            inner = match.group(1)
            if not inner.strip():
                return "[]"
            nums = [x.strip() for x in inner.split(',')]
            return "[" + ", ".join(nums) + "]"

        json_str = re.sub(r'\[\s*((?:\d+\s*,\s*)*\d+)\s*\]', compact_int_arrays, json_str)

        with open(out, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"Dumped: {out}")

    elif mode == "repack":
        repack_to_bsi(input_file)

    else:
        print(f"Unknown mode: {mode}")
        print("Use 'dump' or 'repack'.")


if __name__ == "__main__":
    main()
