def _msd_radix_sort_inplace(
    list_of_ints: list[int], bit_position: int, begin_index: int, end_index: int
):
    """
    Sort the given list based on the bit at bit_position. Numbers with a
    0 at that position will be at the start of the list, numbers with a
    1 at the end.
    >>> lst = [45, 2, 32, 24, 534, 2932]
    >>> _msd_radix_sort_inplace(lst, 1, 0, 3)
    >>> lst == [32, 2, 45, 24, 534, 2932]
    True
    >>> lst = [0, 2, 1, 3, 12, 10, 4, 90, 54, 2323, 756]
    >>> _msd_radix_sort_inplace(lst, 2, 4, 7)
    >>> lst == [0, 2, 1, 3, 12, 4, 10, 90, 54, 2323, 756]
    True
    """
    if bit_position == 0 or end_index - begin_index <= 1:
        return

    bit_position -= 1

    i = begin_index
    j = end_index - 1
    while i <= j:
        changed = False
        if not (list_of_ints[i] >> bit_position) & 1:
            # found zero at the beginning
            i += 1
            changed = True
        if (list_of_ints[j] >> bit_position) & 1:
            # found one at the end
            j -= 1
            changed = True

        if changed:
            continue

        list_of_ints[i], list_of_ints[j] = list_of_ints[j], list_of_ints[i]
        j -= 1
        if j != i:
            i += 1

    _msd_radix_sort_inplace(list_of_ints, bit_position, begin_index, i)
    _msd_radix_sort_inplace(list_of_ints, bit_position, i, end_index)