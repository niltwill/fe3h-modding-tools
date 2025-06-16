@echo off
for %%f in (script\*.txt) do (
    text-events.py build "%%f"
)