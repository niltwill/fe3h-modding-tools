import json
import os
import struct
import sys

# Dict definitions
enumMonth = {
    0: "GreatTreeMoon",
    1: "GreatTreeMoon_",
    2: "HarpstringMoon",
    3: "GarlandMoon",
    4: "BlueSeaMoon",
    5: "VerdantRainMoon",
    6: "HorsebowMoon",
    7: "WyvernMoon",
    8: "RedWolfMoon",
    9: "EtherealMoon",
    10: "GuardianMoon",
    11: "PegasusMoon",
    12: "LoneMoon",
    255: "No_Month_Label",
}

enumTimeOfDay = {
    0: "Daytime",
    1: "Evening",
    2: "Nighttime",
    3: "Daytime2",
    4: "Morning",
    5: "Afternoon",
    6: "Late_Night",
    255: "Not_Used_Label",
}

enumLocation = {
    0: "Audience_Chamber_0",
    1: "Advisory_Room_1",
    2: "Meeting_Room_2",
    3: "Reception_Hall_3",
    4: "Entrance_Hall_4",
    5: "Cathedral_5",
    6: "Dormitory_Quarters_6",
    7: "Dormitory_Hallway_7",
    8: "Officers_Academy_8",
    9: "Goddess_Tower_9",
    10: "Training_Grounds_10",
    11: "Dining_Hall_11",
    12: "Courtyard_12",
    13: "Knights_Hall_13",
    14: "Library_14",
    15: "Infirmary_15",
    16: "Star_Terrace_16",
    17: "Star_Terrace_Corridor_17",
    18: "Greenhouse_18",
    19: "Stable_19",
    20: "Captains_Quarter_20",
    21: "Crest_Scholar_Office_21",
    22: "Noble_Guest_Quarters_22",
    23: "Hallway_23",
    24: "Basement_Entrance_24",
    25: "Throne_Room_25",
    26: "Remire_Village_Empire_Terrority_26",
    27: "Black_Eagles_Classroom_27",
    28: "Blue_Eagles_Classroom_28",
    29: "Golden_Deer_Classroom_29",
    30: "Zanado_the_Red_Canyon_30",
    31: "Magdred_Way_31",
    32: "Sealed_Forest_32",
    33: "Conand_Tower_33",
    34: "Dormitory_34",
    35: "Underground_Passage_35",
    36: "Jeritza_Room_36",
    37: "Seteth_Office_37",
    38: "Gronder_Field_38",
    39: "Outer_City_Wall_39",
    40: "The_Darkness_40",
    41: "Holy_Tomb_41",
    42: "Imperial_Palace_42",
    43: "Holy_Mausoleum_43",
    44: "Aillel_Valley_of_Torment_44",
    45: "Great_Brigde_of_Myrddin_45",
    46: "Farming_Village_46",
    47: "Outside_the_Stables_47",
    48: "Knights_Hall_48",
    49: "Fort_Merceus_49",
    50: "Embarr_the_Imperial_Captial_50",
    51: "City_Streets_Embarr_the_Imperial_Capital_51",
    52: "Outside_the_Palace_52",
    53: "Shambhala_the_Underground_City_53",
    54: "Fhirdiad_Kingdom_Captial_54",
    55: "Royal_Castle_Fhridiad_Kingtom_Captial_55",
    56: "City_Streets_Fhirdiad_56",
    57: "City_Streets_Derdriu_the_Aquatic_Captial_57",
    58: "Enbarr_Outskirts_58",
    59: "Great_Bridge_of_Myrddin_Outskirts_59",
    60: "Outside_the_Palace_Wall_Enbarr_60",
    61: "Imperial_Army_Encampment_61",
    62: "Monastery_Outskirts_62",
    63: "Admininstrative_Office_Arianrhod_Fortress_City_63",
    64: "Tailtean_Plains_64",
    65: "Outside_the_Castle_Gate_Fhirdiad_65",
    66: "Goneril_Terrority_Fodlan_Throat_Outskirt_66",
    67: "Personal_Quarter_67", 
    68: "Duscur_Region_Kingdom_Territory_68",
    69: "Farming_Village_Kingdom_Territory_69",
    70: "Brionac_Plataeu_70",
    71: "Officers_Room_71",
    72: "Forest_Hyrm_Territory_72",
    73: "Temporary_Encampment_73",
    74: "Forest_Brigid_74",
    75: "Gloucester_Territory_75",
    76: "Rhodos_Coast_76",
    77: "Riegan_Territory_77",
    78: "Garreg_Mach_Monastery_78",
    79: "Fhirdiad_Kingdom_Capitial_Year_1181_79",
    80: "Fhirdiad_Kingdom_Capitial_Year_1176_80",
    81: "Outside_the_Gates_Deridru_81",
    82: "Throme_Room_Enbarr_82",
    83: "Near_Conand_Tower_83",
    84: "Near_Fort_Merceus_84",
    85: "Common_Room_85",
    86: "Abyssian_Classroom_86",
    87: "Blank_87",
    88: "Abyssian_Residents_88",
    89: "Passageway_89",
    90: "The_Depths_90",
    91: "Underground_Arena_91",
    92: "Underneath_Garreg_Mach_92",
    93: "Somewhere_in_the_Monastery_93",
    65535: "No_Location_Label",
}

enumSupport = {
    0: "C",
    1: "C_Plus",
    2: "B",
    3: "B_Plus",
    4: "A",
    5: "A_Plus",
    6: "S",
    7: "Goddess_Tower",
    255: "Not_Used",
}

enumByleth_Gender = {
    0: "Male",
    1: "Female",
    15: "Both",
    255: "Not_Byleth",
}

enumAvailability = {
    0: "Pre_Timeskip_Only",
    1: "Post_Timeskip_Only",
    2: "Wedding_Ring_Needed", # educated guess
    255: "No_Restriction",
}

enumFlag = {
    255: "Not_Used",
}

enumFlagShort = {
    65535: "Not_Used",
}

enumNames = {
    0: "Byleth_0",
    1: "Byleth_1",
    2: "Edelgard_2",
    3: "Dimitri_3",
    4: "Claude_4",
    5: "Hubert_5",
    6: "Ferdinand_6",
    7: "Linhardt_7",
    8: "Caspar_8",
    9: "Bernadetta_9",
    10: "Dorothea_10",
    11: "Petra_11",
    12: "Dedue_12",
    13: "Felix_13",
    14: "Ashe_14",
    15: "Sylvain_15",
    16: "Mercedes_16",
    17: "Annette_17",
    18: "Ingrid_18",
    19: "Lorenz_19",
    20: "Raphael_20",
    21: "Ignatz_21",
    22: "Lysithea_22",
    23: "Marianne_23",
    24: "Hilda_24",
    25: "Leonie_25",
    26: "Seteth_26",
    27: "Flayn_27",
    28: "Hanneman_28",
    29: "Manuela_29",
    30: "Gilbert_30",
    31: "Alois_31",
    32: "Catherine_32",
    33: "Shamir_33",
    34: "Cyril_34",
    35: "Jeralt_35",
    36: "Rhea_36",
    37: "Sothis_37",
    1040: "Yuri",
    1041: "Balthus",
    1042: "Constance",
    1043: "Hapi",
    1044: "ChurchOfSeirosDudeWithMinorCrest",
    1045: "Jeritza_Playable",
    1046: "Anna_Playable",
    65535: "No_Character",
}

enumBGM = {
    0: "FodlanWinds_0",
    2: "TearingThroughHeaven_2",
    4: "RoarOfDominion_4",
    6: "ChasingDaybreak_6",
    8: "TheLongRoad_8",
    10: "BlueSkiesAndABattle_10",
    12: "BetweenHeavenAndEarth_12",
    14: "GodShatteringStar_14",
    16: "AFuneralOfFlowers_16",
    18: "TheApexOfTheWorld_18",
    20: "TempestOfSeasons_20",
    24: "ShambhalaAreaSeventeenRedux_24",
    26: "DwellingsOfTheAncientGods_26",
    28: "CorridorOfTheTempest_28",
    32: "WrathStrike_32",
    34: "TheVergeOfDeath_34",
    38: "PathsThatWillNeverCross_38",
    40: "IndomitableWill_40",
    44: "TheShackledWolves_44",
    46: "AtWhatCost_46",
    48: "MapBattleBossReservedA_48",
    49: "MapBattleBossReservedB_49",
    50: "MapBattleBossReservedC_50",
    51: "MapBattleBossReservedD_51",
    52: "TheSpiritDais_52",
    54: "GuardianOfStarlight_54",
    55: "GazingAtSirius_55",
    56: "SongOfTheNabateans_56",
    57: "ThoseWhoSowDarkness_57",
    58: "RespiteAndSunlight_58",
    59: "AGentleBreeze_59",
    60: "BeneathTheBanner_60",
    61: "RecollectionAndRegret_61",
    62: "SomewhereToBelong_62",
    63: "CalmWindsOverGentleWaters_63",
    64: "Tactics_64",
    65: "Anxiety_65",
    66: "TheLeadersPath_66",
    67: "KingOfLions_67",
    68: "GoldenDeerAndCrescentMoon_68",
    69: "ADarkSign_69",
    70: "Spiderweb_70",
    71: "MaskOfFire_71",
    72: "DarkCloudsGather_72",
    73: "ArcanaCode_73",
    74: "BeyondTheCrossroads_74",
    75: "ALonelyFigure_75",
    76: "AVowRemembered_76",
    77: "APlaceToRest_77",
    78: "APromise_78",
    79: "Unfulfilled_79",
    81: "FunnyFootsteps_81",
    82: "WordsToBelieveIn_82",
    83: "LearningLessons_83",
    84: "SeekingNewHeights_84",
    85: "HungryMarch_85",
    86: "BattleOnTheWaterfront_86",
    88: "HopeAsAMelody_88",
    89: "TeatimeJoy_89",
    91: "Farewell_91",
    92: "WhiteHeronWaltz_92",
    95: "BurningUp_95",
    96: "ThreeHousesMainTheme_96",
    97: "TheCrestOfFlames_97",
    98: "LifeAtGarregMachMonastery_98",
    99: "BrokenRoutine_99",
    100: "ScalesOfTheGoddess_100",
    104: "AsSwiftAsWind_104",
    105: "AsFierceAsFire_105",
    106: "TheLandBelovedByTheGoddess_106",
    107: "ThreeCrowns_107",
    108: "TheDreamIsOver_108",
    110: "AStarInTheMorningSky_110",
    111: "StillHorizon_111",
    112: "TheEdgeOfDawn_112",
    113: "TheColorOfSunrise_113",
    114: "TheEdgeOfDawnSeasonsOfWarfare_114",
    65535: "Not_Set",
}

enumEventNames = {
    0: "EV0_Dreams_of_a_Throne",
    1: "EV1_A_Skirmish_at_Dawn",
    2: "EV2_The_Girl_on_the_Throne",
    3: "EV3_An_Unexpected_Reunion",
    4: "EV4_The_Prince_the_Princess_and_the_Heir",
    5: "EV5_Return_of_the_Former_Captain",
    6: "EV6_A_Pair_of_Professors",
    7: "EV7_The_Crest_Scholar_s_Office",
    8: "EV8_A_Critical_Choice",
    9: "EV9_Students_of_the_Black_Eagles",
    10: "EV10_Students_of_the_Blue_Lions",
    11: "EV11_Students_of_the_Golden_Deer",
    12: "EV12_The_Black_Eagles_Rise",
    13: "EV13_The_Blue_Lions_Rise",
    14: "EV14_The_Golden_Deer_Rise",
    15: "EV15_The_Mock_Battle_Black_Eagles",
    16: "EV16_The_Mock_Battle_Blue_Lions",
    17: "EV17_The_Mock_Battle_Golden_Deer",
    18: "EV18_Report_Great_Tree_Moon",
    19: "EV19_The_Fugitive_Bandits",
    20: "EV20_A_True_Battle_Black_Eagles",
    21: "EV21_A_True_Battle_Blue_Lions",
    22: "EV22_A_True_Battle_Golden_Deer",
    23: "EV23_Memories_of_the_Red_Canyon",
    24: "EV24_First_Mission_Black_Eagles",
    25: "EV25_First_Mission_Blue_Lions",
    26: "EV26_First_Mission_Golden_Deer",
    27: "EV27_Report_Harpstring_Moon",
    28: "EV28_Rumors_of_a_Rebellion",
    29: "EV29_Into_the_Fog_Black_Eagles",
    30: "EV30_Into_the_Fog_Blue_Lions",
    31: "EV31_Into_the_Fog_Golden_Deer",
    32: "EV32_A_Harsh_Reality_Black_Eagles",
    33: "EV33_A_Harsh_Reality_Blue_Lions",
    34: "EV34_A_Harsh_Reality_Golden_Deer",
    35: "EV35_Report_Garland_Moon",
    36: "EV36_The_Enemy_s_Aim_Black_Eagles",
    37: "EV37_The_Enemy_s_Aim_Blue_Lions",
    38: "EV38_The_Enemy_s_Aim_Golden_Deer",
    39: "EV39_The_Goddess_s_Rite_of_Rebirth_Black_Eagles",
    40: "EV40_The_Goddess_s_Rite_of_Rebirth_Blue_Lions",
    41: "EV41_The_Goddess_s_Rite_of_Rebirth_Golden_Deer",
    42: "EV42_Judgment_Black_Eagles",
    43: "EV43_Judgment_Blue_Lions",
    44: "EV44_Judgment_Golden_Deer",
    45: "EV45_Slithering_in_the_Dark",
    46: "EV46_Report_Blue_Sea_Moon",
    47: "EV47_The_Stolen_Relic_Black_Eagles",
    48: "EV48_The_Stolen_Relic_Blue_Lions",
    49: "EV49_The_Stolen_Relic_Golden_Deer",
    50: "EV50_Tower_in_a_Storm_Black_Eagles",
    51: "EV51_Tower_in_a_Storm_Blue_Lions",
    52: "EV52_Tower_in_a_Storm_Golden_Deer",
    53: "EV53_The_Lance_of_Ruin",
    54: "EV54_Crests_The_Good_and_the_Bad_Black_Eagles",
    55: "EV55_Crests_The_Good_and_the_Bad_Blue_Lions",
    56: "EV56_Crests_The_Good_and_the_Bad_Golden_Deer",
    57: "EV57_Report_Verdant_Rain_Moon",
    58: "EV58_Vanished_Black_Eagles",
    59: "EV59_Vanished_Blue_Lions",
    60: "EV60_Vanished_Golden_Deer",
    61: "EV61_Suspicious_Behavior_Blue_Lions",
    62: "EV62_Investigation_Black_Eagles",
    63: "EV63_Investigation_Blue_Lions",
    64: "EV64_Investigation_Golden_Deer",
    65: "EV65_Discovery_Black_Eagles",
    66: "EV66_Discovery_Blue_Lions",
    67: "EV67_Discovery_Golden_Deer",
    68: "EV68_Rescued_Black_Eagles",
    69: "EV69_Rescued_Blue_Lions",
    70: "EV70_Rescued_Golden_Deer",
    71: "EV71_Blood_Secrets",
    72: "EV72_Report_Horsebow_Moon",
    73: "EV73_Battle_of_the_Eagle_and_Lion_Black_Eagles",
    74: "EV74_Battle_of_the_Eagle_and_Lion_Blue_Lions",
    75: "EV75_Battle_of_the_Eagle_and_Lion_Golden_Deer",
    76: "EV76_Field_of_Three_Black_Eagles",
    77: "EV77_Field_of_Three_Blue_Lions",
    78: "EV78_Field_of_Three_Golden_Deer",
    79: "EV79_Commendable_Effort_Black_Eagles",
    80: "EV80_Commendable_Effort_Blue_Lions",
    81: "EV81_Commendable_Effort_Golden_Deer",
    82: "EV82_Trust_in_the_Professor_Black_Eagles",
    83: "EV83_Trust_in_the_Professor_Blue_Lions",
    84: "EV84_Trust_in_the_Professor_Golden_Deer",
    85: "EV85_Report_Wyvern_Moon",
    86: "EV86_A_New_Disaster",
    87: "EV87_Another_Mystery_Black_Eagles",
    88: "EV88_Another_Mystery_Blue_Lions",
    89: "EV89_Another_Mystery_Golden_Deer",
    90: "EV90_Village_Tragedy_Black_Eagles",
    91: "EV91_Village_Tragedy_Blue_Lions",
    92: "EV92_Village_Tragedy_Golden_Deer",
    93: "EV93_The_Flame_Emperor_Appears",
    94: "EV94_The_Mystery_Deepens_Black_Eagles",
    95: "EV95_The_Mystery_Deepens_Blue_Lions",
    96: "EV96_The_Mystery_Deepens_Golden_Deer",
    97: "EV97_Report_Red_Wolf_Moon",
    98: "EV98_Chapel_in_Ruin",
    99: "EV99_A_Night_of_Promises_Black_Eagles",
    100: "EV100_A_Night_of_Promises_Blue_Lions",
    101: "EV101_A_Night_of_Promises_Golden_Deer",
    102: "EV102_Childhood_Memories_Blue_Lions",
    103: "EV103_To_the_Goddess_Tower",
    104: "EV104_Rhea_and_Sothis",
    105: "EV105_An_Urgent_Report",
    106: "EV106_Father_s_Diary",
    107: "EV107_Father_s_Diary_Blue_Lions",
    108: "EV108_Report_Ethereal_Moon",
    109: "EV109_A_Form_of_Grief_Black_Eagles",
    110: "EV110_The_Enemy_Blue_Lions",
    111: "EV111_A_Form_of_Grief_Golden_Deer",
    112: "EV112_Forest_Invitation_Black_Eagles",
    113: "EV113_Forest_Invitation_Blue_Lions",
    114: "EV114_Forest_Invitation_Golden_Deer",
    115: "EV115_The_Sealed_Forest_Black_Eagles",
    116: "EV116_The_Sealed_Forest_Blue_Lions",
    117: "EV117_The_Sealed_Forest_Golden_Deer",
    118: "EV118_The_Missing_Professor_Black_Eagles",
    119: "EV119_The_Missing_Professor_Blue_Lions",
    120: "EV120_The_Missing_Professor_Golden_Deer",
    121: "EV121_Sothis_The_Beginning",
    122: "EV122_Transformation_Black_Eagles",
    123: "EV123_Transformation_Blue_Lions",
    124: "EV124_Transformation_Golden_Deer",
    125: "EV125_Report_Guardian_Moon",
    126: "EV126_True_Identity",
    127: "EV127_Coronation_Black_Eagles",
    128: "EV128_Deep_Underground_Blue_Lions",
    129: "EV129_Deep_Underground_Golden_Deer",
    130: "EV130_The_Holy_Tomb_Black_Eagles",
    131: "EV131_The_Holy_Tomb_Blue_Lions",
    132: "EV132_The_Holy_Tomb_Golden_Deer",
    133: "EV133_Fateful_Farewell_Black_Eagles",
    134: "EV134_Fateful_Farewell_Blue_Lions",
    135: "EV135_Fateful_Farewell_Golden_Deer",
    136: "EV136_Whispers_of_War_Black_Eagles",
    137: "EV137_Whispers_of_War_Blue_Lions",
    138: "EV138_Whispers_of_War_Golden_Deer",
    139: "EV139_The_Imperial_Army_Rises",
    140: "EV140_To_War_Black_Eagles",
    141: "EV141_To_War_Blue_Lions",
    142: "EV142_To_War_Golden_Deer",
    143: "EV143_The_White_Heron_Cup",
    144: "EV144_Like_the_Silver_Snow",
    145: "EV145_Aftermath_of_War",
    146: "EV146_The_Fallen_Monastery",
    147: "EV147_Begin_Again",
    148: "EV148_In_the_Heart_of_Fodlan",
    149: "EV149_Imperial_Invasion",
    150: "EV150_The_Resistance_Army_s_Objective",
    151: "EV151_Rhea_s_Whereabouts",
    152: "EV152_Seeking_Reinforcements",
    153: "EV153_Valley_of_Torment",
    154: "EV154_Joining_Forces",
    155: "EV155_War_Council_Pegasus_Moon",
    156: "EV156_Time_to_Advance",
    157: "EV157_The_Great_Bridge",
    158: "EV158_A_Visitor",
    159: "EV159_Revival",
    160: "EV160_Beneath_the_Azure_Moon",
    161: "EV161_Aftermath_of_War",
    162: "EV162_The_Fallen_Monastery",
    163: "EV163_Five_Years_Lost",
    164: "EV164_In_the_Heart_of_Fodlan",
    165: "EV165_Imperial_Invasion",
    166: "EV166_Monsters",
    167: "EV167_War_Council_Guardian_Moon",
    168: "EV168_Seeking_Reinforcements",
    169: "EV169_Valley_of_Torment",
    170: "EV170_Joining_Forces",
    171: "EV171_War_Council_Pegasus_Moon",
    172: "EV172_Entrusting_the_Future",
    173: "EV173_The_Great_Bridge",
    174: "EV174_Back_to_Base",
    175: "EV175_Field_of_Destiny",
    176: "EV176_Battlefield",
    177: "EV177_Revenge",
    178: "EV178_A_Reason_to_Live",
    179: "EV179_The_Verdant_Wind_at_Dawn",
    180: "EV180_Aftermath_of_War",
    181: "EV181_The_Fallen_Monastery",
    182: "EV182_War_Council_Ethereal_Moon",
    183: "EV183_In_the_Heart_of_Fodlan",
    184: "EV184_Imperial_Invasion",
    185: "EV185_The_Resistance_Army_s_Objective",
    186: "EV186_The_Alliance_Leader_s_Ambitions",
    187: "EV187_Seeking_Reinforcements",
    188: "EV188_Valley_of_Torment",
    189: "EV189_Joining_Forces",
    190: "EV190_War_Council_Pegasus_Moon",
    191: "EV191_Time_to_Advance",
    192: "EV192_The_Great_Bridge",
    193: "EV193_War_Council_Lone_Moon",
    194: "EV194_Field_of_Destiny",
    195: "EV195_Battlefield",
    196: "EV196_Battle_Fallout",
    197: "EV197_Mysterious_Figures",
    198: "EV198_War_Council_Great_Tree_Moon",
    199: "EV199_The_Impregnable_Fortress",
    200: "EV200_The_Death_Knight",
    201: "EV201_The_Only_Path",
    202: "EV202_A_Decisive_Battle",
    203: "EV203_The_Streets_of_Enbarr",
    204: "EV204_The_Archbishop_s_Whereabouts",
    205: "EV205_The_Imperial_Palace",
    206: "EV206_Our_True_Enemy",
    207: "EV207_Ambitions_in_the_Dark",
    208: "EV208_To_Shambhala",
    209: "EV209_An_Underground_World",
    210: "EV210_The_Price_of_Victory",
    211: "EV211_Rampage",
    212: "EV212_What_Must_Be_Done",
    213: "EV213_Home",
    214: "EV214_Taking_Back_Fhirdiad",
    215: "EV215_Night_of_the_Feast",
    216: "EV216_The_Alliance_in_Peril",
    217: "EV217_To_the_Rescue",
    218: "EV218_The_End_of_the_Alliance",
    219: "EV219_Resolve",
    220: "EV220_The_Impregnable_Fortress",
    221: "EV221_The_Death_Knight",
    222: "EV222_War_Council_Blue_Sea_Moon",
    223: "EV223_Death_and_Truth",
    224: "EV224_Questions_and_Answers",
    225: "EV225_The_Imperial_Palace",
    226: "EV226_Oil_and_Water",
    227: "EV227_The_Impregnable_Fortress",
    228: "EV228_The_Death_Knight",
    229: "EV229_Javelins_of_Light",
    230: "EV230_The_Alliance_Leader_s_True_Identity",
    231: "EV231_A_Decisive_Battle",
    232: "EV232_The_Streets_of_Enbarr",
    233: "EV233_The_Archbishop_s_Whereabouts",
    234: "EV234_The_Imperial_Palace",
    235: "EV235_Our_True_Enemy",
    236: "EV236_Bloodstained_History",
    237: "EV237_Ambitions_in_the_Dark",
    238: "EV238_War_Council_Blue_Sea_Moon",
    239: "EV239_To_Shambhala",
    240: "EV240_An_Underground_World",
    241: "EV241_The_Price_of_Victory",
    242: "EV242_The_King_of_Liberation",
    243: "EV243_For_Fodlan",
    244: "EV244_Choice_and_Consequence",
    245: "EV245_Path_of_Thorns",
    246: "EV246_The_Black_Eagle_Strike_Force",
    247: "EV247_Against_the_World",
    248: "EV248_Revival",
    249: "EV249_Edelgard",
    250: "EV250_A_Path_of_Crimson_Flowers",
    251: "EV251_Disquiet",
    252: "EV252_War_Council_Ethereal_Moon",
    253: "EV253_The_Aquatic_Capital",
    254: "EV254_The_Truth_About_Relics",
    255: "EV255_The_Alliance_Leader_s_Scheme",
    256: "EV256_Triumphant_Return",
    257: "EV257_Facing_the_Kingdom",
    258: "EV258_Surprise_Attack",
    259: "EV259_War_Council_Pegasus_Moon",
    260: "EV260_The_Fortress_City",
    261: "EV261_Raid",
    262: "EV262_Agarthan_Technology",
    263: "EV263_War_Council_Lone_Moon",
    264: "EV264_Preparing_for_the_Final_Battle",
    265: "EV265_Field_of_Revenge",
    266: "EV266_The_Kingdom_Capital",
    267: "EV267_Stolen_Time",
    268: "EV268_The_Final_Battle",
    269: "EV269_The_Immaculate_One",
    270: "EV270_conversation_event_placeholder_2",
    271: "EV271_conversation_event_placeholder_3",
    272: "EV272_conversation_event_placeholder_4",
    273: "EV273_conversation_event_placeholder_5",
    274: "EV274_conversation_event_placeholder_6",
    275: "EV275_conversation_event_placeholder_7",
    276: "EV276_conversation_event_placeholder_8",
    277: "EV277_conversation_event_placeholder_9",
    278: "EV278_conversation_event_placeholder_10",
    279: "EV279_conversation_event_placeholder_11",
    280: "Pre_Eternal_Guardian",
    281: "Post_Eternal_Guardian",
    282: "Pre_The_Silver_Maiden",
    283: "Post_The_Silver_Maiden",
    284: "Pre_Insurmountable",
    285: "Post_Insurmountable",
    286: "Pre_The_Sleeping_Sand_Legend",
    287: "Post_The_Sleeping_Sand_Legend",
    288: "Pre_Tales_of_the_Red_Canyon",
    289: "Post_Tales_of_the_Red_Canyon",
    290: "Pre_War_for_the_Weak",
    291: "Post_War_for_the_Weak",
    292: "Pre_True_Chivalry",
    293: "Post_True_Chivalry",
    294: "Pre_Falling_Short_of_Heaven",
    295: "Post_Falling_Short_of_Heaven",
    296: "Pre_The_Forgotten",
    297: "Post_The_Forgotten",
    298: "Pre_The_Face_Beneath",
    299: "Post_The_Face_Beneath",
    300: "Pre_Weathervanes_of_Fodlan",
    301: "Post_Weathervanes_of_Fodlan",
    302: "Pre_Rumored_Nuptials",
    303: "Post_Rumored_Nuptials",
    304: "Pre_Darkness_Beneath_the_Water",
    305: "Post_Darkness_Beneath_the_Water",
    306: "Pre_Retribution",
    307: "Post_Retribution",
    308: "Pre_Legend_of_the_Lake",
    309: "Post_Legend_of_the_Lake",
    310: "Pre_Foreign_Land_and_Sky",
    311: "Post_Foreign_Land_and_Sky",
    312: "Pre_Land_of_the_Golden_Deer",
    313: "Post_Land_of_the_Golden_Deer",
    314: "Pre_Death_Toll",
    315: "Post_Death_Toll",
    316: "Pre_Forgotten_Hero",
    317: "Post_Forgotten_Hero",
    318: "Pre_Dividing_the_World",
    319: "Post_Dividing_the_World",
    320: "Pre_An_Ocean_View",
    321: "Post_An_Ocean_View",
    322: "Pre_Oil_and_Water",
    323: "Post_Oil_and_Water",
    324: "Pre_Sword_and_Shield_of_Seiros",
    325: "Post_Sword_and_Shield_of_Seiros",
    1288: "Pre_The_Secret_Merchant",
    1289: "Post_The_Secret_Merchant",
    1290: "Pre_Black_Market_Scheme",
    1291: "Post_Black_Market_Scheme",
    1292: "Pre_A_Cursed_Relic",
    1293: "Post_A_Cursed_Relic",
    65535: "No_Event",
}

def get_enum_label(enum_dict, key):
    return enum_dict.get(key, f"{key}")

def get_enum_value(enum_dict, label):
    for key, value in enum_dict.items():
        if value == label:
            return key
    try:
        # If it's already a numeric string like "3", return as int
        return int(label)
    except ValueError:
        raise ValueError(f"Label '{label}' not found in enum.")

def parse_6163_file(filename):
    with open(filename, 'rb') as f:
        # Header
        number_of_entries, unknown1, unknown2, unknown3 = struct.unpack('<4I', f.read(16))
        #print(f"Header: Entries={number_of_entries}, Unknowns=({unknown1}, {unknown2}, {unknown3})")

        entries = []
        for i in range(number_of_entries):
            entry_data = f.read(28)
            (
                entry_number,
                music,
                e_unknown1,
                location_label,
                time_of_day_label,
                month_label,
                support_partner_1,
                support_partner_2,
                support_rank,
                byleth_gender,
                unk_flag,
                availability_flag,
                e_unknown2,
                ch_avail_be, ch_avail_bl, ch_avail_gd, ch_avail_church,
                ch_deadline_be, ch_deadline_bl, ch_deadline_gd, ch_deadline_church,
                separator
            ) = struct.unpack('<4H2B2H14B', entry_data)

            entry = {
                "EntryNumber": get_enum_label(enumEventNames, entry_number),
                "Music": get_enum_label(enumBGM, music),
                "Unknown1": get_enum_label(enumFlagShort, e_unknown1),
                "LocationLabel": get_enum_label(enumLocation, location_label),
                "TimeOfDayLabel": get_enum_label(enumTimeOfDay, time_of_day_label),
                "MonthLabel": get_enum_label(enumMonth, month_label),
                "SupportPartner1": get_enum_label(enumNames, support_partner_1),
                "SupportPartner2": get_enum_label(enumNames, support_partner_2),
                "SupportRank": get_enum_label(enumSupport, support_rank),
                "BylethGender": get_enum_label(enumByleth_Gender, byleth_gender),
                "UnknownFlag": get_enum_label(enumFlag, unk_flag),
                "Availability": get_enum_label(enumAvailability, availability_flag),
                "Unknown2": get_enum_label(enumFlag, e_unknown2),
                "ChapterAvailability": {
                    "BE": get_enum_label(enumFlag, ch_avail_be),
                    "BL": get_enum_label(enumFlag, ch_avail_bl),
                    "GD": get_enum_label(enumFlag, ch_avail_gd),
                    "Church": get_enum_label(enumFlag, ch_avail_church)
                },
                "ChapterDeadline": {
                    "BE": get_enum_label(enumFlag, ch_deadline_be),
                    "BL": get_enum_label(enumFlag, ch_deadline_bl),
                    "GD": get_enum_label(enumFlag, ch_deadline_gd),
                    "Church": get_enum_label(enumFlag, ch_deadline_church)
                }
            }
            entries.append(entry)

        return {
            "Header": {
                "NumberOfEntries": number_of_entries,
                "Unknown1": unknown1,
                "Unknown2": unknown2,
                "Unknown3": unknown3
            },
            "Entries": entries
        }

def rebuild_6163_file(json_data, output_filename):
    with open(output_filename, 'wb') as f:
        header = json_data["Header"]
        entries = json_data["Entries"]

        # Write header
        number_of_entries = header["NumberOfEntries"]
        unknown1 = header["Unknown1"]
        unknown2 = header["Unknown2"]
        unknown3 = header["Unknown3"]
        f.write(struct.pack('<4I', number_of_entries, unknown1, unknown2, unknown3))

        for entry in entries:
            entry_number = get_enum_value(enumEventNames, entry["EntryNumber"])
            music = get_enum_value(enumBGM, entry["Music"])
            e_unknown1 = get_enum_value(enumFlagShort, entry["Unknown1"])
            location_label = get_enum_value(enumLocation, entry["LocationLabel"])
            time_of_day_label = get_enum_value(enumTimeOfDay, entry["TimeOfDayLabel"])
            month_label = get_enum_value(enumMonth, entry["MonthLabel"])
            support_partner_1 = get_enum_value(enumNames, entry["SupportPartner1"])
            support_partner_2 = get_enum_value(enumNames, entry["SupportPartner2"])
            support_rank = get_enum_value(enumSupport, entry["SupportRank"])
            byleth_gender = get_enum_value(enumByleth_Gender, entry["BylethGender"])
            unk_flag = get_enum_value(enumFlag, entry["UnknownFlag"])
            availability_flag = get_enum_value(enumAvailability, entry["Availability"])
            e_unknown2 = get_enum_value(enumFlag, entry["Unknown2"])
            routes = ["BE", "BL", "GD", "Church"]
            ch_avail = { key: get_enum_value(enumFlag, entry["ChapterAvailability"][key]) for key in routes }
            ch_deadline = { key: get_enum_value(enumFlag, entry["ChapterDeadline"][key]) for key in routes }
            separator = 0 # always zero

            # Pack and write the 28-byte entry
            entry_data = struct.pack(
                '<4H2B2H14B',
                entry_number,
                music,
                e_unknown1,
                location_label,
                time_of_day_label,
                month_label,
                support_partner_1,
                support_partner_2,
                support_rank,
                byleth_gender,
                unk_flag,
                availability_flag,
                e_unknown2,
                ch_avail["BE"],
                ch_avail["BL"],
                ch_avail["GD"],
                ch_avail["Church"],
                ch_deadline["BE"],
                ch_deadline["BL"],
                ch_deadline["GD"],
                ch_deadline["Church"],
                separator
            )
            f.write(entry_data)

        # Align to 16 bytes (add some padding as needed)
        current_size = f.tell()
        padding_needed = (16 - (current_size % 16)) % 16
        if padding_needed:
            f.write(b'\x00' * padding_needed)

def main():
    if len(sys.argv) < 3:
        print("FE3H: IN_EventBaseInfo (support-related)")
        print("For file: romfs/patch4/nx/event/talk_event/data/IN_EventBaseInfo.bin")
        print("")
        print("Usage:")
        print("  To dump:   python mod-IN_EventBaseInfo.py dump <IN_EventBaseInfo.bin> [output.json]")
        print("  To build:  python mod-IN_EventBaseInfo.py build <input.json> [IN_EventBaseInfo.bin]")
        print("")
        print("Note: The output file is optional, if not given, the input's filename will be used in the same directory")
        return

    mode = sys.argv[1].lower()
    input_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) >= 4 else None

    if not os.path.isfile(input_file):
        print(f"Error: File '{input_file}' does not exist.")
        return

    if mode == "dump":
        if not output_file:
            output_file = os.path.splitext(input_file)[0] + ".json"

        try:
            result = parse_6163_file(input_file)
            with open(output_file, 'w', encoding='utf-8') as out_file:
                json.dump(result, out_file, indent=2)
            print(f"Dumped to: {output_file}")
        except Exception as e:
            print(f"Error while dumping: {e}")

    elif mode == "build":
        if not output_file:
            output_file = os.path.splitext(input_file)[0] + ".bin"

        try:
            with open(input_file, 'r', encoding='utf-8') as jf:
                parsed_json = json.load(jf)
                rebuild_6163_file(parsed_json, output_file)
                print(f"Built to: {output_file}")
        except Exception as e:
            print(f"Error while building: {e}")

    else:
        print("Unknown mode. Use 'dump' or 'build'.")

if __name__ == "__main__":
    main()
