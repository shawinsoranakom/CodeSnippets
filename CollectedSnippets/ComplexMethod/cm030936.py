def flat_conjoin(gs):  # rename to conjoin to run tests with this instead
    n = len(gs)
    values = [None] * n
    iters  = [None] * n
    _StopIteration = StopIteration  # make local because caught a *lot*
    i = 0
    while 1:
        # Descend.
        try:
            while i < n:
                it = iters[i] = gs[i]().__next__
                values[i] = it()
                i += 1
        except _StopIteration:
            pass
        else:
            assert i == n
            yield values

        # Backtrack until an older iterator can be resumed.
        i -= 1
        while i >= 0:
            try:
                values[i] = iters[i]()
                # Success!  Start fresh at next level.
                i += 1
                break
            except _StopIteration:
                # Continue backtracking.
                i -= 1
        else:
            assert i < 0
            break