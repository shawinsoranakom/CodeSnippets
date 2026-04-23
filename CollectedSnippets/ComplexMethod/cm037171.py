def monitor_workers():
            # Poll with a timeout rather than blocking on ray.wait()
            # because a blocking call would segfault if Ray is torn down
            # while this thread is inside it.
            while not _should_stop() and ray.is_initialized():
                try:
                    done, _ = ray.wait(run_refs, num_returns=1, timeout=5.0)
                except Exception:
                    logger.exception(
                        "RayWorkerMonitor: unexpected error, exiting monitor thread"
                    )
                    return
                if not done or _should_stop():
                    continue

                dead_ranks = [ref_to_rank[r] for r in done]
                executor = self_ref()
                if not executor:
                    return
                executor.is_failed = True
                logger.error(
                    "RayWorkerProc rank=%s died unexpectedly, shutting down executor.",
                    dead_ranks,
                )
                executor.shutdown()
                if executor.failure_callback is not None:
                    callback = executor.failure_callback
                    executor.failure_callback = None
                    callback()
                return