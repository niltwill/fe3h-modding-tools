Just put the `DATA0.bin` and `DATA1.bin` files (which you can get from the game's dumped RomFS) to this directory, then run the `extractIndexNum.py` from CMD window (you need Python installed for this).
It will take a while, extracting between 26-27 thousands of files. Also make sure to have enough free space on your drive!

After that's done, also run the `filelist.py` to map the indexes to known filenames and put them in directories (if you don't want to suffer!).

However, for the romfs extracted from DLCs, do not run `filelist.py`, only `extractIndexNum.py`!