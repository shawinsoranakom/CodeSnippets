def _worker(executor_reference, ctx, work_queue):
    try:
        ctx.initialize()
    except BaseException:
        _base.LOGGER.critical('Exception in initializer:', exc_info=True)
        executor = executor_reference()
        if executor is not None:
            executor._initializer_failed()
        return
    try:
        while True:
            try:
                work_item = work_queue.get_nowait()
            except queue.Empty:
                # attempt to increment idle count if queue is empty
                executor = executor_reference()
                if executor is not None:
                    executor._idle_semaphore.release()
                del executor
                work_item = work_queue.get(block=True)

            if work_item is not None:
                work_item.run(ctx)
                # Delete references to object. See GH-60488
                del work_item
                continue

            executor = executor_reference()
            # Exit if:
            #   - The interpreter is shutting down OR
            #   - The executor that owns the worker has been collected OR
            #   - The executor that owns the worker has been shutdown.
            if _shutdown or executor is None or executor._shutdown:
                # Flag the executor as shutting down as early as possible if it
                # is not gc-ed yet.
                if executor is not None:
                    executor._shutdown = True
                # Notice other workers
                work_queue.put(None)
                return
            del executor
    except BaseException:
        _base.LOGGER.critical('Exception in worker', exc_info=True)
    finally:
        ctx.finalize()