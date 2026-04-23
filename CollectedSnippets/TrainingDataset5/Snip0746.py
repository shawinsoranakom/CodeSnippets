def _count_cross_inversions(p, q):

    r = []
    i = j = num_inversion = 0
    while i < len(p) and j < len(q):
        if p[i] > q[j]:
            num_inversion += len(p) - i
            r.append(q[j])
            j += 1
        else:
            r.append(p[i])
            i += 1

    if i < len(p):
        r.extend(p[i:])
    else:
        r.extend(q[j:])

    return r, num_inversion
