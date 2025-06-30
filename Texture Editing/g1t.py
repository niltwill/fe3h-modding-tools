# G1T Platform enumeration
G1T_PLATFORMS = {
    0: "PS2", 1: "PS3", 2: "X360", 3: "NWii", 4: "NDS", 5: "N3DS",
    6: "PSVita", 7: "Android", 8: "iOS", 9: "NWiiU", 10: "Windows",
    11: "PS4", 12: "XOne", 13: "NSwitch"
}

# G1T Subsystem enumeration
G1T_SUBSYSTEMS = {
    0: "Generic", 1: "PS4", 2: "PSVita", 3: "PS3", 4: "Xbox"
}

# Comprehensive G1T type mapping
G1T_TYPE_MAP = {
    # Standard formats
    0x00: {"format": "RGBA8", "fourcc": None, "bpp": 32, "block_size": 1},
    0x01: {"format": "BGRA8", "fourcc": None, "bpp": 32, "block_size": 1},
    0x02: {"format": "R32", "fourcc": None, "bpp": 32, "block_size": 1},
    0x03: {"format": "RGBA16", "fourcc": None, "bpp": 64, "block_size": 1},
    0x04: {"format": "RGBA32F", "fourcc": None, "bpp": 128, "block_size": 1},
    
    # Modern DXT
    0x59: {"format": "DXT1", "fourcc": b'DXT1', "bpp": 4, "block_size": 8},
    0x5B: {"format": "DXT5", "fourcc": b'DXT5', "bpp": 8, "block_size": 16},
    0x5C: {"format": "BC4", "fourcc": b'ATI1', "bpp": 4, "block_size": 8},
    0x5D: {"format": "BC5", "fourcc": b'ATI2', "bpp": 8, "block_size": 16},
    0x5E: {"format": "BC6H", "fourcc": b'BC6H', "bpp": 8, "block_size": 16},
    0x5F: {"format": "BC7", "fourcc": b'BC7 ', "bpp": 8, "block_size": 16},
    
    # Morton swizzled modern formats
    0x60: {"format": "DXT1_Morton", "fourcc": b'DXT1', "bpp": 4, "block_size": 8, "morton": True},
    0x62: {"format": "DXT5_Morton", "fourcc": b'DXT5', "bpp": 8, "block_size": 16, "morton": True},
    0x63: {"format": "BC4_Morton", "fourcc": b'BC4U', "bpp": 4, "block_size": 8, "morton": True},
    0x64: {"format": "BC5_Morton", "fourcc": b'BC5U', "bpp": 8, "block_size": 16, "morton": True},
    0x65: {"format": "BC6H_Morton", "fourcc": b'BC6H', "bpp": 8, "block_size": 16, "morton": True},
    0x66: {"format": "BC7_Morton", "fourcc": b'BC7 ', "bpp": 8, "block_size": 16, "morton": True},
    
    # DXT formats
    0x06: {"format": "DXT1", "fourcc": b'DXT1', "bpp": 4, "block_size": 8},
    0x07: {"format": "DXT3", "fourcc": b'DXT3', "bpp": 8, "block_size": 16},
    0x08: {"format": "DXT5", "fourcc": b'DXT5', "bpp": 8, "block_size": 16},
    
    # Morton swizzled formats
    0x0A: {"format": "BGRA8_Morton", "fourcc": None, "bpp": 32, "block_size": 1, "morton": True},
    0x0B: {"format": "R32_Morton", "fourcc": None, "bpp": 32, "block_size": 1, "morton": True},
    0x0F: {"format": "A8", "fourcc": None, "bpp": 8, "block_size": 1},
    
    # DXT Morton swizzled
    0x10: {"format": "DXT1_Morton", "fourcc": b'DXT1', "bpp": 4, "block_size": 8, "morton": True},
    0x12: {"format": "DXT5_Morton", "fourcc": b'DXT5', "bpp": 8, "block_size": 16, "morton": True},
    
    # 16-bit formats
    0x34: {"format": "BGR565", "fourcc": None, "bpp": 16, "block_size": 1},
    0x35: {"format": "ABGR1555", "fourcc": None, "bpp": 16, "block_size": 1},
    0x36: {"format": "ABGR4444", "fourcc": None, "bpp": 16, "block_size": 1},
    
    # More DXT variants
    0x3C: {"format": "DXT1", "fourcc": b'DXT1', "bpp": 4, "block_size": 8},
    0x3D: {"format": "DXT1", "fourcc": b'DXT1', "bpp": 4, "block_size": 8},
    
    # 3DS formats
    0x47: {"format": "3DS_RGB", "fourcc": None, "bpp": 32, "block_size": 1},
    0x48: {"format": "3DS_RGBA", "fourcc": None, "bpp": 32, "block_size": 1},
    
    # Mobile formats
    0x56: {"format": "ETC1_RGB", "fourcc": None, "bpp": 4, "block_size": 8},
    0x57: {"format": "PVRTC", "fourcc": None, "bpp": 2, "block_size": 8},
    0x58: {"format": "PVRTC_4", "fourcc": None, "bpp": 4, "block_size": 8},
    
    # Special ETC formats
    0x6F: {"format": "ETC1_RGB_Special", "fourcc": None, "bpp": 4, "block_size": 8, "special": True},
    0x71: {"format": "ETC1_RGBA", "fourcc": None, "bpp": 8, "block_size": 16},
    
    # ASTC format
    0x7D: {"format": "ASTC", "fourcc": None, "bpp": 8, "block_size": 16, "astc": True},
}

ASTC_BLOCK_SIZE_TO_SUBFORMAT = {
    (4, 4): 0,
    (5, 4): 1,
    (5, 5): 2,
    (6, 5): 3,
    (6, 6): 4,
    (8, 5): 5,
    (8, 6): 6,
    (8, 8): 7,
    (10, 5): 8,
    (10, 6): 9,
    (10, 8): 10,
    (10, 10): 11,
    (12, 10): 12,
    (12, 12): 13
}
