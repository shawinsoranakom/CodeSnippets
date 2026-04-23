def random_puzzle(assignments=17):
    """
    Make a random puzzle with N or more assignments. Restart on contradictions.
    Note the resulting puzzle is not guaranteed to be solvable, but empirically
    about 99.8% of them are solvable. Some have multiple solutions.
    """
    values = dict.fromkeys(squares, digits)
    for s in shuffled(squares):
        if not assign(values, s, random.choice(values[s])):
            break
        ds = [values[s] for s in squares if len(values[s]) == 1]
        if len(ds) >= assignments and len(set(ds)) >= 8:
            return "".join(values[s] if len(values[s]) == 1 else "." for s in squares)
    return random_puzzle(assignments)