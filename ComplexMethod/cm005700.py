def generate_attention_matrix_from_mask(
    words, mask, img_token="<img>", sliding_window=None, token_type_ids=None, image_seq_length=None
):
    """
    Generates an attention matrix from a given attention mask.

    Optionally applies a sliding window mask (e.g., for Gemma2/3) and
    marks regions where image tokens occur based on the specified `img_token`.
    """
    mask = mask.int()
    if mask.ndim == 3:
        mask = mask[0, :, :]
    if mask.ndim == 4:
        mask = mask[0, 0, :, :]

    n = len(words)
    max_word_length = max(len(repr(word)) for word in words)
    first_img_idx = 0
    output = []

    for i, k in enumerate(words):
        if k == img_token and not first_img_idx:
            first_img_idx = i
            mask[i, i] = 2  # Mark yellow regions
        if first_img_idx > 0 and (k != img_token or i == n - 1):
            if i == n - 1:
                i += 1
            mask[first_img_idx:i, first_img_idx:i] = 2  # Mark yellow regions
            first_img_idx = 0

    # Generate sliding window mask (size = 4), excluding img_token
    sliding_window_mask = None
    if sliding_window is not None:
        sliding_window_mask = [[1 if (0 <= i - j < sliding_window) else 0 for j in range(n)] for i in range(n)]

    row_dummy = " ".join(
        f"{YELLOW}{BLACK_SQUARE}{RESET}"
        if mask[0, j]
        else f"{GREEN}{BLACK_SQUARE}{RESET}"
        if j == 0
        else BLACK_SQUARE
        if mask[0, j]
        else WHITE_SQUARE
        for j in range(n)
    )

    if token_type_ids is not None:
        is_special = token_type_ids == 1
        token_type_buckets = torch.where(
            (token_type_ids.cumsum(-1) % 5 + is_special).bool(), token_type_ids.cumsum(-1), 0
        )
        boundaries = torch.arange(0, image_seq_length + 1, image_seq_length)
        token_type_buckets = torch.bucketize(token_type_buckets, boundaries=boundaries)

    # Print headers
    legend = f"{GREEN}{BLACK_SQUARE}{RESET}: i == j (diagonal)   {YELLOW}{BLACK_SQUARE}{RESET}: token_type_ids"
    output.append(" " + legend)
    f_string = " " * (max_word_length + 5) + "Attention Matrix".ljust(len(row_dummy) // 2)
    if sliding_window is not None:
        f_string += "Sliding Window Mask"
    output.append(f_string)

    vertical_header = []
    for idx, word in enumerate(words):
        if mask[idx, idx] == 2:
            vertical_header.append([f"{YELLOW}{k}{RESET}" for k in list(str(idx).rjust(len(str(n))))])
        else:
            vertical_header.append(list(str(idx).rjust(len(str(n)))))

    vertical_header = list(map(list, zip(*vertical_header)))  # Transpose

    for row in vertical_header:
        output.append(
            (max_word_length + 5) * " " + " ".join(row) + "    |    " + " ".join(row)
            if sliding_window is not None
            else ""
        )
    for i, word in enumerate(words):
        word_repr = repr(word).ljust(max_word_length)
        colored_word = f"{YELLOW}{word_repr}{RESET}" if img_token in word else word_repr
        row_display = " ".join(
            f"{YELLOW}{BLACK_SQUARE}{RESET}"
            if img_token in words[j] and mask[i, j] and img_token in word
            else f"{GREEN}{BLACK_SQUARE}{RESET}"
            if i == j
            else BLACK_SQUARE
            if mask[i, j]
            else WHITE_SQUARE
            for j in range(n)
        )
        sliding_window_row = ""
        if sliding_window is not None:
            sliding_window_row = " ".join(
                f"{YELLOW}{BLACK_SQUARE}{RESET}"
                if img_token in words[j] and img_token in word and token_type_buckets[0, i] == token_type_buckets[0, j]
                else f"{GREEN}{BLACK_SQUARE}{RESET}"
                if i == j
                else BLACK_SQUARE
                if sliding_window_mask[i][j]
                else WHITE_SQUARE
                for j in range(n)
            )

        output.append(f"{colored_word}: {str(i).rjust(2)} {row_display}    |    {sliding_window_row}")

    return "\n".join(output)