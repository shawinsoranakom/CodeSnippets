def octal_to_hex(octal: str) -> str:

    if not isinstance(octal, str):
        raise TypeError("Expected a string as input")
    if octal.startswith("0o"):
        octal = octal[2:]
    if octal == "":
        raise ValueError("Empty string was passed to the function")
    if any(char not in "01234567" for char in octal):
        raise ValueError("Not a Valid Octal Number")

    decimal = 0
    for char in octal:
        decimal <<= 3
        decimal |= int(char)

    hex_char = "0123456789ABCDEF"

    revhex = ""
    while decimal:
        revhex += hex_char[decimal & 15]
        decimal >>= 4

    return "0x" + revhex[::-1]

