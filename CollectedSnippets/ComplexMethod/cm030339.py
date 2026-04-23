def _handle_results(outqueue, get, cache):
        thread = threading.current_thread()

        while 1:
            try:
                task = get()
            except (OSError, EOFError):
                util.debug('result handler got EOFError/OSError -- exiting')
                return

            if thread._state != RUN:
                assert thread._state == TERMINATE, "Thread not in TERMINATE"
                util.debug('result handler found thread._state=TERMINATE')
                break

            if task is None:
                util.debug('result handler got sentinel')
                break

            job, i, obj = task
            try:
                cache[job]._set(i, obj)
            except KeyError:
                pass
            task = job = obj = None

        while cache and thread._state != TERMINATE:
            try:
                task = get()
            except (OSError, EOFError):
                util.debug('result handler got EOFError/OSError -- exiting')
                return

            if task is None:
                util.debug('result handler ignoring extra sentinel')
                continue
            job, i, obj = task
            try:
                cache[job]._set(i, obj)
            except KeyError:
                pass
            task = job = obj = None

        if hasattr(outqueue, '_reader'):
            util.debug('ensuring that outqueue is not full')
            # If we don't make room available in outqueue then
            # attempts to add the sentinel (None) to outqueue may
            # block.  There is guaranteed to be no more than 2 sentinels.
            try:
                for i in range(10):
                    if not outqueue._reader.poll():
                        break
                    get()
            except (OSError, EOFError):
                pass

        util.debug('result handler exiting: len(cache)=%s, thread._state=%s',
              len(cache), thread._state)