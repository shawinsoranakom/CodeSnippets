def _sanity_check_splits(splits_1, splits_2, is_class, filename):
    """Check the two (inner) block structures of the corresponding code block given by `split_code_into_blocks` match.

    For the case of `class`, they must be of one of the following 3 cases:

        - a single block without name:

            class foo:
                a = 1

        - a consecutive sequence of (1 or more) blocks with name

            class foo:

                def f(x):
                    return x

        - a block without name, followed by a consecutive sequence of (1 or more) blocks with name

            class foo:
                a = 1

                def f(x):
                    return x

                def g(x):
                    return None

    The 2 code snippets that give `splits_1` and `splits_2` have to be in the same case to pass this check, but the
    number of blocks with name in the consecutive sequence is not taken into account.

    For the case of `function or method`, we don't require it to be in one of the above 3 cases. However, the structure
    of`splits_1` and `splits_2` have to match exactly. In particular, the number of blocks with name in a consecutive
    sequence is taken into account.
    """
    block_names_1 = []
    block_names_2 = []

    for block in splits_1[1:]:
        if block[0].startswith("_block_without_name_"):
            block_names_1.append("block_without_name")
        elif not block[0].startswith("_empty_block_") and (
            not is_class or len(block_names_1) == 0 or block_names_1[-1].startswith("block_without_name")
        ):
            block_names_1.append("block_with_name")

    for block in splits_2[1:]:
        if block[0].startswith("_block_without_name_"):
            block_names_2.append("block_without_name")
        elif not block[0].startswith("_empty_block_") and (
            not is_class or len(block_names_2) == 0 or block_names_2[-1].startswith("block_without_name")
        ):
            block_names_2.append("block_with_name")

    if is_class:
        if block_names_1 not in [
            ["block_without_name"],
            ["block_with_name"],
            ["block_without_name", "block_with_name"],
        ]:
            raise ValueError(
                f"""Class defined in {filename} doesn't have the expected structure.
                See the docstring of `_sanity_check_splits` in the file `utils/check_copies.py`""",
            )

    if block_names_1 != block_names_2:
        raise ValueError(f"In {filename}, two code blocks expected to be copies have different structures.")