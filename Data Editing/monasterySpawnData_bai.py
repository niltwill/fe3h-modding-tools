import json, struct, os, re, sys
from BaiCharNames import BAI_CHAR_NAMES

ENTRY_SIZE = 0x18  # 24 bytes per entity record
BLOCK_COUNT = 3
REGISTRY_START = 250  # entries 250-262 = patrol region registry

# Rotation enum from BaiEnums.bt
FACING_NAMES = {0:'RightSlightlyUp', 1:'UpSlightlyRight', 2:'Up', 3:'UpLeft',
                4:'Left', 5:'DownLeft', 6:'Down', 7:'DownRight'}
BEHAVIOR_NAMES = {0:'Static', 1:'SpecialNPC', 2:'Patrol_A', 3:'Patrol_B', 7:'WaypointEnd'}
MOVE_MODE_NAMES = {0:'Static', 1:'WalkToInteract', 2:'Patrol'}

# BaiCharNames (enum)
def get_char_name(bai_char_id: int) -> str:
    """BAI char_id = game CharID + 1. Strip trailing _N for readability."""
    raw = BAI_CHAR_NAMES.get(bai_char_id, f'unk_bai{bai_char_id}')
    return re.sub(r'_\d+$', '', raw)

CHAR_NAME_TO_ID = {}
for char_id, char_name in BAI_CHAR_NAMES.items():
    cleaned_name = re.sub(r'_\\d+$', '', char_name)
    CHAR_NAME_TO_ID[char_name] = char_id
    CHAR_NAME_TO_ID[cleaned_name] = char_id

def get_char_id(char_name):
    if isinstance(char_name, int):
        return char_name
    cleaned_name = re.sub(r'_\\d+$', '', char_name)
    return CHAR_NAME_TO_ID.get(cleaned_name, 0)


###

def parse_entity(e):
    """Parse one 24-byte entity record with the correct struct."""
    char_id, padding, spawn_x, spawn_z, facing_packed = struct.unpack_from('<HHffH', e, 0)
    ub = e[14:24]   # bytes 14..23 = the 10 behavior bytes
    facing_dir  = facing_packed & 0xFF
    record_type = (facing_packed >> 8) & 0xFF
    return {
        'char_id': BAI_CHAR_NAMES.get(char_id, f'unk_bai{char_id}'),
        'padding': padding,
        'spawn_x': spawn_x,
        'spawn_z': spawn_z,
        'facing_dir': facing_dir,
        'record_type': record_type,
        'unavailable_flag': ub[0],  # byte 14: +0x0E
        'behavior_type': ub[1],     # byte 15: +0x0F
        'patrol_angle': ub[2],      # byte 16: +0x10
        'unk_0x14C': ub[3],         # byte 17: +0x11
        'waypoint_flags': ub[4],    # byte 18: +0x12
        'unk_0x14E': ub[5],         # byte 19: +0x13
        'move_mode': ub[6],         # byte 20: +0x14
        'unk_D2_bit5': ub[7],       # byte 21: +0x15
        'loop_flag': ub[8],         # byte 22: +0x16
        'unk_0x150': ub[9],         # byte 23: +0x17
    }


def parse_registry_slot(slot4):
    """Decode one 4-byte slot from the patrol region registry."""
    return {'warp_dest_A': slot4[0], 'warp_dest_B': slot4[1],
            'block_flag': slot4[2], 'seq_counter': slot4[3]}


def parse_bai_file(filename):
    with open(filename, 'rb') as f:
        data = f.read()

    type_hdr, magic, reserved = struct.unpack_from('<3I', data, 0)
    block_offsets = list(struct.unpack_from('<3I', data, 12))

    FILE_DATA_START = 0x18

    blocks = []
    registries = []
    trailing_list = []

    for i in range(BLOCK_COUNT):
        block_start = FILE_DATA_START + block_offsets[i]
        if i < BLOCK_COUNT - 1:
            block_total = (FILE_DATA_START + block_offsets[i + 1]) - block_start
        else:
            block_total = len(data) - block_start

        trailing_size = 20
        entry_bytes = block_total - trailing_size
        num_entries = entry_bytes // ENTRY_SIZE  # should be 263

        records = []
        registry_slots = []

        for j in range(num_entries):
            off = block_start + j * ENTRY_SIZE
            e = data[off:off + ENTRY_SIZE]

            if j >= REGISTRY_START:
                # Entries 250-262: patrol region registry (6 slots per entry)
                for slot_i in range(6):
                    slot4 = e[slot_i * 4: slot_i * 4 + 4]
                    registry_slots.append(parse_registry_slot(slot4))
            else:
                records.append(parse_entity(e))

        # Trailing patrol entity indices
        trailing_off = block_start + num_entries * ENTRY_SIZE
        trailing_indices = list(struct.unpack_from('>5I', data, trailing_off))

        blocks.append(records)
        registries.append(registry_slots)
        trailing_list.append(trailing_indices)

    return {
        'Header': {'TypeHeader': hex(type_hdr), 'Magic': hex(magic), 'Reserved': hex(reserved)},
        'BlockOffsets': [hex(o) for o in block_offsets],
        'Blocks': blocks,
        'PatrolRegistries': registries,   # 3 registries, each 78 slots
        'TrailingPatrolIndices': trailing_list,
    }


def find_terminator(records):
    for i, r in enumerate(records):
        if r['record_type'] > 3:
            return i
    return len(records)


def print_block_summary(parsed, block_idx):
    block = parsed['Blocks'][block_idx]
    trailing = parsed['TrailingPatrolIndices'][block_idx]
    registry = parsed['PatrolRegistries'][block_idx]

    term = find_terminator(block)
    print(f"  Block {block_idx}: {term} real records (terminator at index {term})")

    from collections import Counter
    bt = Counter(r['behavior_type'] for r in block[:term])
    print(f"  Behavior types: {dict(bt)}")
    print(f"  Trailing patrol indices: {trailing}")

    non_empty = [(s['seq_counter'], s['warp_dest_A'], s['warp_dest_B'])
                 for s in registry if s['warp_dest_A'] != 0 or s['warp_dest_B'] != 0]
    print(f"  Registry: {len(non_empty)} non-empty slots (out of 78)")
    print(f"  First 5 real records:")
    for r in block[:5]:
        btype = BEHAVIOR_NAMES.get(r['behavior_type'], f'?{r["behavior_type"]}')
        facing = FACING_NAMES.get(r['facing_dir'], f'?{r["facing_dir"]}')
        char_name = get_char_name(r['char_id'])
        extra = ''
        if r['patrol_angle']: extra += f' angle={r["patrol_angle"]}'
        if r['unavailable_flag']: extra += ' [HIDDEN]'
        print(f"    char={char_name} x={r['spawn_x']:8.1f} z={r['spawn_z']:8.1f} "
              f"face={facing} type={btype}{extra}")


def repack_to_bai(json_file, output_file=None):
    with open(json_file, 'r', encoding='utf-8') as f:
        parsed = json.load(f)

    block_offsets = [int(o, 16) for o in parsed['BlockOffsets']]
    FILE_DATA_START = 0x18

    last_off = FILE_DATA_START + block_offsets[-1]
    last_entries = len(parsed['Blocks'][-1]) + 13  # 250 real records + 13 registry entries
    buf_size = last_off + last_entries * ENTRY_SIZE + 20
    buf = bytearray(buf_size)

    hdr = parsed['Header']
    struct.pack_into('<I', buf, 0, int(hdr['TypeHeader'], 16))
    struct.pack_into('<I', buf, 4, int(hdr['Magic'], 16))
    struct.pack_into('<I', buf, 8, int(hdr['Reserved'], 16))
    for i, o in enumerate(block_offsets):
        struct.pack_into('<I', buf, 12 + i * 4, o)

    for i in range(BLOCK_COUNT):
        block_start = FILE_DATA_START + block_offsets[i]
        records = parsed['Blocks'][i]
        registry = parsed['PatrolRegistries'][i]
        trailing = parsed['TrailingPatrolIndices'][i]

        # Write entity records (0..249)
        for j, r in enumerate(records):
            off = block_start + j * ENTRY_SIZE
            facing_packed = (r['record_type'] << 8) | (r['facing_dir'] & 0xFF)
            char_id = r['char_id'] if isinstance(r['char_id'], int) else get_char_id(r['char_id'])
            struct.pack_into('<HHffH', buf, off, char_id, r['padding'], r['spawn_x'], r['spawn_z'], facing_packed)
            buf[off+14:off+24] = bytes([
                r['unavailable_flag'], r['behavior_type'], r['patrol_angle'],
                r['unk_0x14C'], r['waypoint_flags'], r['unk_0x14E'],
                r['move_mode'], r['unk_D2_bit5'], r['loop_flag'], r['unk_0x150']
            ])

        # Write registry entries (250..262)
        for ri, slot in enumerate(registry):
            entry_i = ri // 6
            slot_i  = ri %  6
            off = block_start + (REGISTRY_START + entry_i) * ENTRY_SIZE + slot_i * 4
            buf[off] = slot['warp_dest_A'] & 0xFF
            buf[off+1] = slot['warp_dest_B'] & 0xFF
            buf[off+2] = slot['block_flag'] & 0xFF
            buf[off+3] = slot['seq_counter'] & 0xFF

        # Write trailing
        trail_off = block_start + (REGISTRY_START + 13) * ENTRY_SIZE
        for idx in (trailing or [0, 0, 0, 0, 0]):
            struct.pack_into('>I', buf, trail_off, idx)
            trail_off += 4

    if not output_file:
        output_file = os.path.splitext(json_file)[0] + '.bai'
    with open(output_file, 'wb') as f:
        f.write(buf)
    print(f'Repacked: {output_file}')


def main():
    if len(sys.argv) < 3:
        print('Usage:')
        print('  python monasterySpawnData_bai.py dump <input.bai>')
        print('  python monasterySpawnData_bai.py repack <input.json>')
        print('  python monasterySpawnData_bai.py summary <input.bai>')
        return

    mode = sys.argv[1].lower()
    input_file = sys.argv[2]

    if mode == 'dump':
        parsed = parse_bai_file(input_file)
        out = os.path.splitext(input_file)[0] + '.json'
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(parsed, f, indent=2)
        print(f'Dumped: {out}')

    elif mode == 'summary':
        parsed = parse_bai_file(input_file)
        print(f'File: {input_file}')
        print(f'Header: {parsed["Header"]}')
        print(f'BlockOffsets: {parsed["BlockOffsets"]}')
        print()
        for i in range(BLOCK_COUNT):
            print_block_summary(parsed, i)
            print()

    elif mode == 'repack':
        repack_to_bai(input_file)

if __name__ == '__main__':
    main()
