def reverse_bwt(bwt_string: str, idx_original_string: int) -> str:
    if not isinstance(bwt_string, str):
        raise TypeError("The parameter bwt_string type must be str.")
    if not bwt_string:
        raise ValueError("The parameter bwt_string must not be empty.")
    try:
        idx_original_string = int(idx_original_string)
    except ValueError:
        raise TypeError(
            "The parameter idx_original_string type must be int or passive"
            " of cast to int."
        )
    if idx_original_string < 0:
        raise ValueError("The parameter idx_original_string must not be lower than 0.")
    if idx_original_string >= len(bwt_string):
        raise ValueError(
            "The parameter idx_original_string must be lower than len(bwt_string)."
        )

    ordered_rotations = [""] * len(bwt_string)
    for _ in range(len(bwt_string)):
        for i in range(len(bwt_string)):
            ordered_rotations[i] = bwt_string[i] + ordered_rotations[i]
        ordered_rotations.sort()
    return ordered_rotations[idx_original_string]
