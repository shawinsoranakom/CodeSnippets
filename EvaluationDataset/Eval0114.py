def rgb_to_cmyk(r_input: int, g_input: int, b_input: int) -> tuple[int, int, int, int]:

    if (
        not isinstance(r_input, int)
        or not isinstance(g_input, int)
        or not isinstance(b_input, int)
    ):
        msg = f"Expected int, found {type(r_input), type(g_input), type(b_input)}"
        raise ValueError(msg)

    if not 0 <= r_input < 256 or not 0 <= g_input < 256 or not 0 <= b_input < 256:
        raise ValueError("Expected int of the range 0..255")

    r = r_input / 255
    g = g_input / 255
    b = b_input / 255

    k = 1 - max(r, g, b)

    if k == 1:  
        return 0, 0, 0, 100

    c = round(100 * (1 - r - k) / (1 - k))
    m = round(100 * (1 - g - k) / (1 - k))
    y = round(100 * (1 - b - k) / (1 - k))
    k = round(100 * k)

    return c, m, y, k
