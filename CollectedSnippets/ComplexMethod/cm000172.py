def reverse_bwt(bwt_string: str, idx_original_string: int) -> str:
    """
    :param bwt_string: The string returned from bwt algorithm execution
    :param idx_original_string: A 0-based index of the string that was used to
    generate bwt_string at ordered rotations list
    :return: The string used to generate bwt_string when bwt was executed
    :raises TypeError: If the bwt_string parameter type is not str
    :raises ValueError: If the bwt_string parameter is empty
    :raises TypeError: If the idx_original_string type is not int or if not
    possible to cast it to int
    :raises ValueError: If the idx_original_string value is lower than 0 or
    greater than len(bwt_string) - 1

    >>> reverse_bwt("BNN^AAA", 6)
    '^BANANA'
    >>> reverse_bwt("aaaadss_c__aa", 3)
    'a_asa_da_casa'
    >>> reverse_bwt("mnpbnnaaaaaa", 11)
    'panamabanana'
    >>> reverse_bwt(4, 11)
    Traceback (most recent call last):
        ...
    TypeError: The parameter bwt_string type must be str.
    >>> reverse_bwt("", 11)
    Traceback (most recent call last):
        ...
    ValueError: The parameter bwt_string must not be empty.
    >>> reverse_bwt("mnpbnnaaaaaa", "asd") # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
        ...
    TypeError: The parameter idx_original_string type must be int or passive
    of cast to int.
    >>> reverse_bwt("mnpbnnaaaaaa", -1)
    Traceback (most recent call last):
        ...
    ValueError: The parameter idx_original_string must not be lower than 0.
    >>> reverse_bwt("mnpbnnaaaaaa", 12) # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
        ...
    ValueError: The parameter idx_original_string must be lower than
    len(bwt_string).
    >>> reverse_bwt("mnpbnnaaaaaa", 11.0)
    'panamabanana'
    >>> reverse_bwt("mnpbnnaaaaaa", 11.4)
    'panamabanana'
    """
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