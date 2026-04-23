def compute(a_i, k, i, n):
    """
    same as next_term(a_i, k, i, n) but computes terms without memoizing results.
    """
    if i >= n:
        return 0, i
    if k > len(a_i):
        a_i.extend([0 for _ in range(k - len(a_i))])

    # note: a_i -> b * 10^k + c
    # ds_b -> digitsum(b)
    # ds_c -> digitsum(c)
    start_i = i
    ds_b, ds_c, diff = 0, 0, 0
    for j in range(len(a_i)):
        if j >= k:
            ds_b += a_i[j]
        else:
            ds_c += a_i[j]

    while i < n:
        i += 1
        addend = ds_c + ds_b
        diff += addend
        ds_c = 0
        for j in range(k):
            s = a_i[j] + addend
            addend, a_i[j] = divmod(s, 10)

            ds_c += a_i[j]

        if addend > 0:
            break

    if addend > 0:
        add(a_i, k, addend)
    return diff, i - start_i