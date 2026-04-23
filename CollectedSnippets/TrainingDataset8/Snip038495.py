def _tearDownAsyncioLoop(self):
        assert self._asyncioTestLoop is not None, "asyncio test loop is not initialized"
        loop = self._asyncioTestLoop
        self._asyncioTestLoop = None
        self._asyncioCallsQueue.put_nowait(None)
        loop.run_until_complete(self._asyncioCallsQueue.join())

        try:
            # cancel all tasks
            to_cancel = asyncio.all_tasks(loop)
            if not to_cancel:
                return

            for task in to_cancel:
                task.cancel()

            loop.run_until_complete(asyncio.gather(*to_cancel, return_exceptions=True))

            for task in to_cancel:
                if task.cancelled():
                    continue
                if task.exception() is not None:
                    loop.call_exception_handler(
                        {
                            "message": "unhandled exception during test shutdown",
                            "exception": task.exception(),
                            "task": task,
                        }
                    )
            # shutdown asyncgens
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            asyncio.set_event_loop(None)
            loop.close()