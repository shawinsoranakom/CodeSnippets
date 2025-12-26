def bin_to_hexadecimal(binary_str: str) -> str:

    binary_str = str(binary_str).strip()

    if not binary_str:
        raise ValueError("Empty string was passed to the function")
    is_negative = binary_str[0] == "-"
    binary_str = binary_str[1:] if is_negative else binary_str
    if not all(char in "01" for char in binary_str):
        raise ValueError("Non-binary value was passed to the function")

    binary_str = (
        "0" * (4 * (divmod(len(binary_str), 4)[0] + 1) - len(binary_str)) + binary_str
    )

    hexadecimal = []
    for x in range(0, len(binary_str), 4):
        hexadecimal.append(BITS_TO_HEX[binary_str[x : x + 4]])
    hexadecimal_str = "0x" + "".join(hexadecimal)

    return "-" + hexadecimal_str if is_negative else hexadecimal_str
