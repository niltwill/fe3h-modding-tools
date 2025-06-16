@echo off
for %%f in (script\*.bin) do (
    event-script.py dump "%%f"
)
