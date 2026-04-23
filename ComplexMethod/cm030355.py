def _exhaustive_wait(handles, timeout):
        # Return ALL handles which are currently signalled.  (Only
        # returning the first signalled might create starvation issues.)
        L = list(handles)
        ready = []
        # Windows limits WaitForMultipleObjects at 64 handles, and we use a
        # few for synchronisation, so we switch to batched waits at 60.
        if len(L) > 60:
            try:
                res = _winapi.BatchedWaitForMultipleObjects(L, False, timeout)
            except TimeoutError:
                return []
            ready.extend(L[i] for i in res)
            if res:
                L = [h for i, h in enumerate(L) if i > res[0] & i not in res]
            timeout = 0
        while L:
            short_L = L[:60] if len(L) > 60 else L
            res = _winapi.WaitForMultipleObjects(short_L, False, timeout)
            if res == WAIT_TIMEOUT:
                break
            elif WAIT_OBJECT_0 <= res < WAIT_OBJECT_0 + len(L):
                res -= WAIT_OBJECT_0
            elif WAIT_ABANDONED_0 <= res < WAIT_ABANDONED_0 + len(L):
                res -= WAIT_ABANDONED_0
            else:
                raise RuntimeError('Should not get here')
            ready.append(L[res])
            L = L[res+1:]
            timeout = 0
        return ready