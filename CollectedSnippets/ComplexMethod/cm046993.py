def _forward_is_unsloth_compiled(model):
    # True iff forward was installed from the Unsloth compile cache directory.
    # __module__ stays as the transformers module, so check co_filename.
    leaves = _unsloth_compile_cache_leaves()

    def check(m):
        if m is None:
            return False
        fwd = getattr(type(m), "forward", None)
        if fwd is None:
            return False
        code = getattr(fwd, "__code__", None)
        fn = getattr(code, "co_filename", "") if code is not None else ""
        fn = fn.replace("\\", "/")
        parts = set(fn.split("/"))
        return any(leaf in parts for leaf in leaves)

    if check(model):
        return True
    seen = set()
    m = model
    for _ in range(4):
        if m is None or id(m) in seen:
            break
        seen.add(id(m))
        nxt = getattr(m, "base_model", None)
        if nxt is None or nxt is m:
            nxt = getattr(m, "model", None)
        if nxt is None or nxt is m:
            break
        if check(nxt):
            return True
        m = nxt
    return False