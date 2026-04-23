def analyze_caches(inputs: list[parser.InputEffect]) -> list[CacheEntry]:
    caches: list[parser.CacheEffect] = [
        i for i in inputs if isinstance(i, parser.CacheEffect)
    ]
    if caches:
        # Middle entries are allowed to be unused. Check first and last caches.
        for index in (0, -1):
            cache = caches[index]
            if cache.name == "unused":
                position = "First" if index == 0 else "Last"
                msg = f"{position} cache entry in op is unused. Move to enclosing macro."
                raise analysis_error(msg, cache.tokens[0])
    return [CacheEntry(i.name, int(i.size)) for i in caches]