def _terminate_pool(cls, taskqueue, inqueue, outqueue, pool, change_notifier,
                        worker_handler, task_handler, result_handler, cache):
        # this is guaranteed to only be called once
        util.debug('finalizing pool')

        # Notify that the worker_handler state has been changed so the
        # _handle_workers loop can be unblocked (and exited) in order to
        # send the finalization sentinel all the workers.
        worker_handler._state = TERMINATE
        change_notifier.put(None)

        task_handler._state = TERMINATE

        util.debug('helping task handler/workers to finish')
        cls._help_stuff_finish(inqueue, task_handler, len(pool))

        if (not result_handler.is_alive()) and (len(cache) != 0):
            raise AssertionError(
                "Cannot have cache with result_handler not alive")

        result_handler._state = TERMINATE
        change_notifier.put(None)
        outqueue.put(None)                  # sentinel

        # We must wait for the worker handler to exit before terminating
        # workers because we don't want workers to be restarted behind our back.
        util.debug('joining worker handler')
        if threading.current_thread() is not worker_handler:
            worker_handler.join()

        # Terminate workers which haven't already finished.
        if pool and hasattr(pool[0], 'terminate'):
            util.debug('terminating workers')
            for p in pool:
                if p.exitcode is None:
                    p.terminate()

        util.debug('joining task handler')
        if threading.current_thread() is not task_handler:
            task_handler.join()

        util.debug('joining result handler')
        if threading.current_thread() is not result_handler:
            result_handler.join()

        if pool and hasattr(pool[0], 'terminate'):
            util.debug('joining pool workers')
            for p in pool:
                if p.is_alive():
                    # worker has not yet exited
                    util.debug('cleaning up worker %d' % p.pid)
                    p.join()