def _run_action(cid, action, end, state):
    if action == 'use':
        if end == 'send':
            _channels.send(cid, b'spam', blocking=False)
            return state.incr()
        elif end == 'recv':
            if not state.pending:
                try:
                    _channels.recv(cid)
                except _channels.ChannelEmptyError:
                    return state
                else:
                    raise Exception('expected ChannelEmptyError')
            else:
                recv_nowait(cid)
                return state.decr()
        else:
            raise ValueError(end)
    elif action == 'close':
        kwargs = {}
        if end in ('recv', 'send'):
            kwargs[end] = True
        _channels.close(cid, **kwargs)
        return state.close()
    elif action == 'force-close':
        kwargs = {
            'force': True,
            }
        if end in ('recv', 'send'):
            kwargs[end] = True
        _channels.close(cid, **kwargs)
        return state.close(force=True)
    else:
        raise ValueError(action)