def get_query_type_frozenset(query: frozenset[int] = Query(...)):
    return ",".join(map(str, sorted(query)))