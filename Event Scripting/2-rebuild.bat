@echo off
for %%f in (script\*.txt) do (
    event-script.py build "%%f"
)