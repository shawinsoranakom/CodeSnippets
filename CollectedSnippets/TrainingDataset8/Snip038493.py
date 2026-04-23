async def _asyncioLoopRunner(self, fut):
        self._asyncioCallsQueue = queue = asyncio.Queue()
        fut.set_result(None)
        while True:
            query = await queue.get()
            queue.task_done()
            if query is None:
                return
            fut, awaitable = query
            try:
                ret = await awaitable
                if not fut.cancelled():
                    fut.set_result(ret)
            except (SystemExit, KeyboardInterrupt):
                raise
            except (BaseException, asyncio.CancelledError) as ex:
                if not fut.cancelled():
                    fut.set_exception(ex)