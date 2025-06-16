So all of these files can be modded now:

* 6159 - IN_GeneralCameraInfo.bin
* 6160.bin
* 6161.bin
* 6162 - IN_FixedCameraInfo.bin
* 6163 - IN_EventBaseInfo.bin
* 6164 - IN_CubeStageBaseInfo.bin
* 6165 - IN_CubeStageChangeInfo.bin
* 6166.bin
* 6167.bin

Note: 6159 and 6162-6165 should be used from `patch4` for the latest version.

These two may be worth a look, perhaps it has to do with stages or battles, ID linking to scenes or something? (This is only a very vague guess.)
 * 6164 - IN_CubeStageBaseInfo.bin
 * 6165 - IN_CubeStageChangeInfo.bin

Other than those, the main point of interest here is `IN_EventBaseInfo.bin`, so use `mod-IN_EventBaseInfo.py` to mod the file for support (level) actions. This seems to define which character can have support with whom. By modding this, you may be able to loosen the support requirements or remove some limitations, things like that.

I'm not really sure how you could add a new support with a new cutscene though. There's likely a data file related to handle supports, don't remember which one.
Perhaps in one of these?
 * fixed_persondata.bin (likely here)
 * fixed_lobby_common.bin
 * fixed_groupworkdata.bin
 * fixed_cut_in.bin

Anyway, what we can infer here is that the entries seem to increment along the same way as the "talk_event" script IDs, for example:

```
6682 - (C)_Byleth_Edelgard.bin -> EntryNumber 341
6683 - (C+)_Byleth_Edelgard.txt -> EntryNumber 342
[...]
7437 - (A)_Shamir_Cyril.txt -> EntryNumber 1096
```

Both of these are 755 overall:
 1. `talk_event` bin files: 7437 - 6682 = 755
 2. `IN_EventBaseInfo` entry numbers: 1096 - 341 = 755

After that entry number, we can see the `UnknownFlags` in action again between "EntryNumber 1097-1168" (71 entries).

The final 'valid' section is at 1169-1252 (83 entries), which seem to involve the `MiscUnknown1` and `MiscUnknown2` flags now (unlike before?), which have values of 0, 4 or 255. It's like a boolean [0=off, 4=on] or ignored value [255], not sure what these are for. `MiscUnknown1` may affect the first partner, and `MiscUnknown2` the second partner.
