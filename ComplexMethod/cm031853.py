def parsecodes(codes, len=len, range=range):

    """ Converts code combinations to either a single code integer
        or a tuple of integers.

        meta-codes (in angular brackets, e.g. <LR> and <RL>) are
        ignored.

        Empty codes or illegal ones are returned as None.

    """
    if not codes:
        return MISSING_CODE
    l = codes.split('+')
    if len(l) == 1:
        return int(l[0],16)
    for i in range(len(l)):
        try:
            l[i] = int(l[i],16)
        except ValueError:
            l[i] = MISSING_CODE
    l = [x for x in l if x != MISSING_CODE]
    if len(l) == 1:
        return l[0]
    else:
        return tuple(l)