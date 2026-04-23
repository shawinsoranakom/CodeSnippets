def pack(structure, data):
    """
    Pack data into hex string with little endian format.
    """
    return struct.pack("<" + structure, *data)