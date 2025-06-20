# FE3H: Event Scripting Tool
# Based on 010 Editor binary templates

import os
import re
import struct
import sys

# Load the custom "enums.py"
import enums

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

#def get_param_info(event_type, param_index):
#    return enums.event_param_definitions.get(event_type, {}).get(param_index, (f"param{param_index}", None))

def get_param_info(event_type, param_index, param_values=None):
    # Exception for event_type 35
    if event_type == 35 and param_index == 2 and param_values:
        cond_val = param_values[0]
        if cond_val == 4:
            return ("route", enums.enumRoute)

    return enums.event_param_definitions.get(event_type, {}).get(param_index, (f"param{param_index}", None))

def format_param_value(value, enum_cls):
    if enum_cls is None:
        return str(value)
    if isinstance(enum_cls, dict):  # Handle dicts as enum maps
        return enum_cls.get(value, f"{value}")
    try:
        return enum_cls(value).name
    except ValueError:
        return f"{value}"

# Read the .bin event script file
def parse_text_events(input_file):
    output_lines = []
    with open(input_file, "rb") as f:
        header = f.read(16)
        num_entries, _, _, _ = struct.unpack("<4I", header)
        #print(f"Number of entries in {input_file}:", num_entries)

        for i in range(num_entries):
            block = f.read(48)
            values = struct.unpack("<12I", block)
            event_type = values[0]
            raw_params = values[1:]

            event_label = enums.known_event_names.get(event_type, "Unknown")
            line = f"#{i} {event_label}: event_type={event_type}"

            formatted_params = []
            for index, value in enumerate(raw_params, 1):
                #param_name, param_enum = get_param_info(event_type, index)
                param_name, param_enum = get_param_info(event_type, index, raw_params)
                value_str = format_param_value(value, param_enum)
                formatted_params.append(f"{param_name}={value_str}")

            if formatted_params:
                line += ", " + ", ".join(formatted_params)

            output_lines.append(line)

    return "\n".join(output_lines)

# Write back to the .bin event script file
def write_text_events(txt_path, bin_path):
    entries = []

    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.startswith("#") or ":" not in line:
                continue

            try:
                _, param_part = line.split(":", 1)
                param_part = param_part.strip()

                kv_pairs = [kv.strip() for kv in param_part.split(",") if "=" in kv]
                kv_dict = dict(kv.split("=", 1) for kv in kv_pairs)

                if "event_type" not in kv_dict:
                    print(f"Warning: Missing event_type in line: {line.strip()}")
                    continue

                try:
                    event_type = int(kv_dict["event_type"])
                except ValueError:
                    print(f"Warning: Invalid event_type in line: {line.strip()}")
                    continue

                values = [event_type]
                param_info = enums.event_param_definitions.get(event_type)

                # Use index 1-11 for param order
                for i in range(1, 12):
                    if param_info and i in param_info:
                        field_name, enum_dict = param_info[i]
                    else:
                        field_name, enum_dict = f"param{i}", None

                    val = kv_dict.get(field_name, "4294967295")

                    if enum_dict:
                        val_int = get_enum_value(enum_dict, val)
                    else:
                        try:
                            val_int = int(val)
                        except ValueError:
                            val_int = 0xFFFFFFFF

                    values.append(val_int)

                entries.append(values)

            except Exception as e:
                print(f"Error parsing line: {line.strip()} → {e}")

    num_entries = len(entries)
    with open(bin_path, "wb") as f:
        f.write(struct.pack("<4I", num_entries, 0, 0, 0))  # 16-byte header
        for entry in entries:
            f.write(struct.pack("<12I", *entry))


def main():
    if len(sys.argv) < 3:
        print("FE3H: An event scripting parser and rebuilder")
        print("You can find them in this folder: nx/event/talk_event/script/*.bin (6341–7437)")
        print("Support scripts are numbered as: 6682–7437")
        print("")
        print("Usage:")
        print("  To dump:   python event-script.py dump <input.bin> [output.txt]")
        print("  To build:  python event-script.py build <input.txt> [output.bin]")
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
            output_file = os.path.splitext(input_file)[0] + ".txt"

        try:
            output_text = parse_text_events(input_file)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output_text + "\n")
            print(f"Dumped to: {output_file}")
        except Exception as e:
            print(f"Error while dumping: {e}")

    elif mode == "build":
        if not output_file:
            output_file = os.path.splitext(input_file)[0] + ".bin"

        try:
            write_text_events(input_file, output_file)
            print(f"Built to: {output_file}")
        except Exception as e:
            print(f"Error while building: {e}")

    else:
        print("Unknown mode. Use 'dump' or 'build'.")

if __name__ == "__main__":
    main()
