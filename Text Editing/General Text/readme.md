Files in these directories should be safe to edit in these places from DATA0.bin and DATA1.bin:

```
nx\event\narration\text\
nx\event\talk_castle\text\
nx\event\talk_event\text\
```

Thankfully, most of the files are located in these dirs, not in the other place.

This location below is experimental when editing (always compare with a hex editor to see if there's a difference, before doing any edit, simply rebuild the JSON to BIN): `nx\event\talk_scinario\text\`

I did not thoroughly test the files there, but I know that this file is a notorious example of having two mismatches (when rebuilding without a change): `10653.bin`
The length of those two values are strangely defined with -2, however changing that means the rest of the values shift instead. You might need to manually change these exceptions at those offsets with the required values after changing these files (IF the new values cause game crash or other strange behaviour/anomalies when you're in at that part of the game). Unfortunately, there may be no rhyme or reason to handle these programatically in a unified way, besides adding an exception list for these problematic filenames at certain offsets (non-standard header values?).
