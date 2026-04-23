def _interleave_lists(lists: List[List[Any]]) -> List[Any]:
    """
    Interleave elements from multiple lists in round-robin fashion.
    Example: [[1,2,3], [a,b], [x,y,z]] -> [1, a, x, 2, b, y, 3, z]
    """
    if not lists:
        return []
    filtered = [lst for lst in lists if lst is not None]
    if not filtered:
        return []
    result: List[Any] = []
    max_len = max(len(lst) for lst in filtered)
    for i in range(max_len):
        for lst in filtered:
            if i < len(lst):
                result.append(lst[i])
    return result