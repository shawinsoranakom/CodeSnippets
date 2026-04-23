def int_to_base36(i):
    """Convert an integer to a base36 string."""
    char_set = "0123456789abcdefghijklmnopqrstuvwxyz"
    if i < 0:
        raise ValueError("Negative base36 conversion input.")
    if i < 36:
        return char_set[i]
    b36_parts = []
    while i != 0:
        i, n = divmod(i, 36)
        b36_parts.append(char_set[n])
    return "".join(reversed(b36_parts))