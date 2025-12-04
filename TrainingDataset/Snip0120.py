def binary_and(a: int, b: int) -> str:
  
    if a < 0 or b < 0:
        raise ValueError("the value of both inputs must be positive")

    a_binary = format(a, "b")
    b_binary = format(b, "b")

    max_len = max(len(a_binary), len(b_binary))

    return "0b" + "".join(
        str(int(char_a == "1" and char_b == "1"))
        for char_a, char_b in zip(a_binary.zfill(max_len), b_binary.zfill(max_len))
    )
