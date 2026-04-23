def eliminate(values, s, d):
    """
    Eliminate d from values[s]; propagate when values or places <= 2.
    Return values, except return False if a contradiction is detected.
    """
    if d not in values[s]:
        return values  ## Already eliminated
    values[s] = values[s].replace(d, "")
    ## (1) If a square s is reduced to one value d2, then eliminate d2 from the peers.
    if len(values[s]) == 0:
        return False  ## Contradiction: removed last value
    elif len(values[s]) == 1:
        d2 = values[s]
        if not all(eliminate(values, s2, d2) for s2 in peers[s]):
            return False
    ## (2) If a unit u is reduced to only one place for a value d, then put it there.
    for u in units[s]:
        dplaces = [s for s in u if d in values[s]]
        if len(dplaces) == 0:
            return False  ## Contradiction: no place for this value
        # d can only be in one place in unit; assign it there
        elif len(dplaces) == 1 and not assign(values, dplaces[0], d):
            return False
    return values