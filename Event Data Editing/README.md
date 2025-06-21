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

Other than those, the main point of interest here is `IN_EventBaseInfo.bin`, so use `mod-IN_EventBaseInfo.py` to mod the file. I'm not really sure how you could add a new support with a new (custom) cutscene though. There's a data file related to handle supports: `fixed_persondata.bin`, which is where one can define additional support. Then the actual support event (and all the other existing events as well) are defined in `IN_EventBaseInfo.bin`.

As a point of interest, what we can infer is that the entries seem to increment along the same way as the "talk_event" script IDs, for example:

```
6682 - (C)_Byleth_Edelgard.bin -> EntryNumber 341
6683 - (C+)_Byleth_Edelgard.txt -> EntryNumber 342
[...]
7437 - (A)_Shamir_Cyril.txt -> EntryNumber 1096
```

Both of these are 755 overall:
 1. `talk_event` bin files: 7437 - 6682 = 755
 2. `IN_EventBaseInfo` entry numbers: 1096 - 341 = 755
