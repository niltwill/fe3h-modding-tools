# FE3H Event Script Editor

A PySide6 GUI editor for Fire Emblem: Three Houses event scripts (.bin).

**Note:** Prebuilt binaries are available for Windows, Linux and macOS in the `dist` folder.

## Requirements

Install Python and PySide6:

```
pip install PySide6
```

## Usage

You can simply use the prebuilt binaries, or you can run it using Python instead:

```
# Launch empty
python main.pyw

# Open a binary directly
python main.pyw path/to/script.bin

# Open a text dump directly
python main.pyw path/to/script.txt
```

## Build

First, make sure you have `pyinstaller` - if it's not installed yet:

```
pip install pyinstaller
```

I don't recommend to use `-F` or `--onefile` with it, since then you won't be able to use the settings JSON file.

---

**On Windows**, to generate an executable, use this command:

```
pyinstaller --windowed --clean --name=fe3h_evscript-editor --icon=fe3h-se-icon.ico --add-data "fe3h-se-icon.ico;." --add-data="editor-settings.json;." main.pyw
```

---

**For Linux**, it depends on the distro. On modern Debian/Ubuntu-based systems, Python is managed by apt and pip refuses system-wide installations to prevent conflicts. So you first need to create a virtual environment (assuming you're in the directory of where these files are):

```
python3 -m venv fe3h-evscript
source fe3h-evscript/bin/activate
pip install pyinstaller PySide6
```

You may also need a package so that the app can run afterward:

```
sudo apt-get install -y libxcb-cursor-dev
```

Then you can run:

```
pyinstaller --windowed --clean --name=fe3h_evscript-editor --icon=fe3h-se-icon.ico --add-data "fe3h-se-icon.ico:." --add-data="editor-settings.json:." main.pyw
```

Once you finish:

```
deactivate fe3h-evscript
```

And you can remove the `fe3h-evscript` folder.

---

**For macOS**, you need to use a slightly different command (and use `python3` and `pip3` instead of `python` and `pip`), since you can't use ICO, only ICNS (assuming you don't have `Pillow` installed):

```
pyinstaller --windowed --clean --name=fe3h_evscript-editor --icon=fe3h-se-icon.icns --add-data "fe3h-se-icon.icns:." --add-data="editor-settings.json:." main.pyw
```

## CLI

If you want CLI usage, you only need three files from here: `event_definitions.py`, `event_enums.py` and `event_script.py` - place them into any arbitrary directory. The main file to use would be `event_script.py`, e.g. `python event_script.py dump <somefile.bin>` and `python event_script.py build <somefile.txt>`. Convenience batch scripts: `1-dump.bat` and `2-rebuild.bat` (using the "script" directory - place the script files there)
