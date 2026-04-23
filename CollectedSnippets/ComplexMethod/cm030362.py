def main(fd):
    '''Run resource tracker.'''
    # protect the process from ^C and "killall python" etc
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    if _HAVE_SIGMASK:
        signal.pthread_sigmask(signal.SIG_UNBLOCK, _IGNORED_SIGNALS)

    for f in (sys.stdin, sys.stdout):
        try:
            f.close()
        except Exception:
            pass

    cache = {rtype: set() for rtype in _CLEANUP_FUNCS.keys()}
    exit_code = 0

    try:
        # keep track of registered/unregistered resources
        with open(fd, 'rb') as f:
            for line in f:
                try:
                    cmd, rtype, name = _decode_message(line)
                    cleanup_func = _CLEANUP_FUNCS.get(rtype, None)
                    if cleanup_func is None:
                        raise ValueError(
                            f'Cannot register {name} for automatic cleanup: '
                            f'unknown resource type {rtype}')

                    if cmd == 'REGISTER':
                        cache[rtype].add(name)
                    elif cmd == 'UNREGISTER':
                        cache[rtype].remove(name)
                    elif cmd == 'PROBE':
                        pass
                    else:
                        raise RuntimeError('unrecognized command %r' % cmd)
                except Exception:
                    exit_code = 3
                    try:
                        sys.excepthook(*sys.exc_info())
                    except:
                        pass
    finally:
        # all processes have terminated; cleanup any remaining resources
        for rtype, rtype_cache in cache.items():
            if rtype_cache:
                try:
                    exit_code = 1
                    if rtype == 'dummy':
                        # The test 'dummy' resource is expected to leak.
                        # We skip the warning (and *only* the warning) for it.
                        pass
                    else:
                        warnings.warn(
                            f'resource_tracker: There appear to be '
                            f'{len(rtype_cache)} leaked {rtype} objects to '
                            f'clean up at shutdown: {rtype_cache}'
                        )
                except Exception:
                    pass
            for name in rtype_cache:
                # For some reason the process which created and registered this
                # resource has failed to unregister it. Presumably it has
                # died.  We therefore unlink it.
                try:
                    try:
                        _CLEANUP_FUNCS[rtype](name)
                    except Exception as e:
                        exit_code = 2
                        warnings.warn('resource_tracker: %r: %s' % (name, e))
                finally:
                    pass

        sys.exit(exit_code)