def eliminate(values, s, d):
    if d not in values[s]:
        return values 
    values[s] = values[s].replace(d, "")
    if len(values[s]) == 0:
        return False 
    elif len(values[s]) == 1:
        d2 = values[s]
        if not all(eliminate(values, s2, d2) for s2 in peers[s]):
            return False
    for u in units[s]:
        dplaces = [s for s in u if d in values[s]]
        if len(dplaces) == 0:
            return False  
        elif len(dplaces) == 1 and not assign(values, dplaces[0], d):
            return False
    return values
