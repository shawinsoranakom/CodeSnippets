def compact_set(l):
    single = []
    tuple = []
    prev = None
    span = 0
    for e in l:
        if prev is None:
            prev = e
            span = 0
            continue
        if prev+span+1 != e:
            if span > 2:
                tuple.append((prev,prev+span+1))
            else:
                for i in range(prev, prev+span+1):
                    single.append(i)
            prev = e
            span = 0
        else:
            span += 1
    if span:
        tuple.append((prev,prev+span+1))
    else:
        single.append(prev)
    if not single and len(tuple) == 1:
        tuple = "range(%d,%d)" % tuple[0]
    else:
        tuple = " + ".join("list(range(%d,%d))" % t for t in tuple)
    if not single:
        return "set(%s)" % tuple
    if not tuple:
        return "set(%r)" % (single,)
    return "set(%r + %s)" % (single, tuple)