@echo off
for %%f in (script\*.bin) do (
    text-events.py dump "%%f"
)
