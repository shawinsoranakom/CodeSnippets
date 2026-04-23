def unpack(structure, data):
    """
    Unpack little endian hexlified binary string into a list.
    """
    return struct.unpack("<" + structure, bytes.fromhex(data))