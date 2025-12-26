def search(values):
    if values is False:
        return False 
    if all(len(values[s]) == 1 for s in squares):
        return values
    _n, s = min((len(values[s]), s) for s in squares if len(values[s]) > 1)
    return some(search(assign(values.copy(), s, d)) for d in values[s])
