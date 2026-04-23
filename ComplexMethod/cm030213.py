def _levenshtein_distance(a, b, max_cost):
    # A Python implementation of Python/suggestions.c:levenshtein_distance.

    # Both strings are the same
    if a == b:
        return 0

    # Trim away common affixes
    pre = 0
    while a[pre:] and b[pre:] and a[pre] == b[pre]:
        pre += 1
    a = a[pre:]
    b = b[pre:]
    post = 0
    while a[:post or None] and b[:post or None] and a[post-1] == b[post-1]:
        post -= 1
    a = a[:post or None]
    b = b[:post or None]
    if not a or not b:
        return _MOVE_COST * (len(a) + len(b))
    if len(a) > _MAX_STRING_SIZE or len(b) > _MAX_STRING_SIZE:
        return max_cost + 1

    # Prefer shorter buffer
    if len(b) < len(a):
        a, b = b, a

    # Quick fail when a match is impossible
    if (len(b) - len(a)) * _MOVE_COST > max_cost:
        return max_cost + 1

    # Instead of producing the whole traditional len(a)-by-len(b)
    # matrix, we can update just one row in place.
    # Initialize the buffer row
    row = list(range(_MOVE_COST, _MOVE_COST * (len(a) + 1), _MOVE_COST))

    result = 0
    for bindex in range(len(b)):
        bchar = b[bindex]
        distance = result = bindex * _MOVE_COST
        minimum = sys.maxsize
        for index in range(len(a)):
            # 1) Previous distance in this row is cost(b[:b_index], a[:index])
            substitute = distance + _substitution_cost(bchar, a[index])
            # 2) cost(b[:b_index], a[:index+1]) from previous row
            distance = row[index]
            # 3) existing result is cost(b[:b_index+1], a[index])

            insert_delete = min(result, distance) + _MOVE_COST
            result = min(insert_delete, substitute)

            # cost(b[:b_index+1], a[:index+1])
            row[index] = result
            if result < minimum:
                minimum = result
        if minimum > max_cost:
            # Everything in this row is too big, so bail early.
            return max_cost + 1
    return result