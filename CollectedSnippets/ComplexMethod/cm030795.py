def dump_dict(before, after, prefix="global"):
    if not verbose or not after:
        return
    max_k = max(len(k) for k in after)
    for k, v in sorted(after.items(), key=lambda i: i[0]):
        if k[:2] == "__":
            continue
        if k == "config":
            dump_dict(before[k], after[k], prefix="config")
            continue
        try:
            if v != before[k]:
                print("{}.{} {!r} (was {!r})".format(prefix, k.ljust(max_k), v, before[k]))
                continue
        except KeyError:
            pass
        print("{}.{} {!r}".format(prefix, k.ljust(max_k), v))