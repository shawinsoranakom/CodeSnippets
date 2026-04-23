def cleanup_threads_and_processes(quiet: bool = True) -> None:
    from localstack.utils.run import kill_process_tree

    for thread in TMP_THREADS:
        if thread:
            try:
                if hasattr(thread, "shutdown"):
                    thread.shutdown()
                    continue
                if hasattr(thread, "kill"):
                    thread.kill()
                    continue
                thread.stop(quiet=quiet)
            except Exception as e:
                LOG.debug("[shutdown] Error stopping thread %s: %s", thread, e)
                if not thread.daemon:
                    LOG.warning(
                        "[shutdown] Non-daemon thread %s may block localstack shutdown", thread
                    )
    for proc in TMP_PROCESSES:
        try:
            kill_process_tree(proc.pid)
            # proc.terminate()
        except Exception as e:
            LOG.debug("[shutdown] Error cleaning up process tree %s: %s", proc, e)
    # clean up async tasks
    try:
        import asyncio

        for task in asyncio.all_tasks():
            try:
                task.cancel()
            except Exception as e:
                LOG.debug("[shutdown] Error cancelling asyncio task %s: %s", task, e)
    except Exception:
        pass
    LOG.debug("[shutdown] Done cleaning up threads / processes / tasks")
    # clear lists
    TMP_THREADS.clear()
    TMP_PROCESSES.clear()