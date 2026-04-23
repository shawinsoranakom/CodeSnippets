def _handle_tasks(taskqueue, put, outqueue, pool, cache):
        thread = threading.current_thread()

        for taskseq, set_length in iter(taskqueue.get, None):
            task = None
            try:
                # iterating taskseq cannot fail
                for task in taskseq:
                    if thread._state != RUN:
                        util.debug('task handler found thread._state != RUN')
                        break
                    try:
                        put(task)
                    except Exception as e:
                        job, idx = task[:2]
                        try:
                            cache[job]._set(idx, (False, e))
                        except KeyError:
                            pass
                else:
                    if set_length:
                        util.debug('doing set_length()')
                        idx = task[1] if task else -1
                        set_length(idx + 1)
                    continue
                break
            finally:
                task = taskseq = job = None
        else:
            util.debug('task handler got sentinel')

        try:
            # tell result handler to finish when cache is empty
            util.debug('task handler sending sentinel to result handler')
            outqueue.put(None)

            # tell workers there is no more work
            util.debug('task handler sending sentinel to workers')
            for p in pool:
                put(None)
        except OSError:
            util.debug('task handler got OSError when sending sentinels')

        util.debug('task handler exiting')