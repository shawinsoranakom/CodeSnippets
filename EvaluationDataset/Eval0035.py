def decrypt_message(key: int, message: str) -> str:
    num_cols = math.ceil(len(message) / key)
    num_rows = key
    num_shaded_boxes = (num_cols * num_rows) - len(message)
    plain_text = [""] * num_cols
    col = 0
    row = 0

    for symbol in message:
        plain_text[col] += symbol
        col += 1

        if (col == num_cols) or (
            (col == num_cols - 1) and (row >= num_rows - num_shaded_boxes)
        ):
            col = 0
            row += 1

    return "".join(plain_text)
