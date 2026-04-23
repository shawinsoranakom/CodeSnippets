def diff_dict(before, after, prefix="global"):
    diff = []
    for k in sorted(before):
        if k[:2] == "__":
            continue
        if k == "config":
            diff_dict(before[k], after[k], prefix="config")
            continue
        if k in after and after[k] != before[k]:
            diff.append((k, before[k], after[k]))
    if not diff:
        return
    max_k = max(len(k) for k, _, _ in diff)
    indent = " " * (len(prefix) + 1 + max_k)
    if verbose:
        for k, b, a in diff:
            if b:
                print("{}.{} -{!r}\n{} +{!r}".format(prefix, k.ljust(max_k), b, indent, a))
            else:
                print("{}.{} +{!r}".format(prefix, k.ljust(max_k), a))