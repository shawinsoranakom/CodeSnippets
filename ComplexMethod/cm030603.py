def run_action(cid, action, end, state, *, hideclosed=True):
    if state.closed:
        if action == 'use' and end == 'recv' and state.pending:
            expectfail = False
        else:
            expectfail = True
    else:
        expectfail = False

    try:
        result = _run_action(cid, action, end, state)
    except _channels.ChannelClosedError:
        if not hideclosed and not expectfail:
            raise
        result = state.close()
    else:
        if expectfail:
            raise ...  # XXX
    return result