def tuplize(seq):
    "Turn all nested sequences to tuples in given sequence."
    if isinstance(seq, (list, tuple)):
        return tuple(tuplize(i) for i in seq)
    return seq