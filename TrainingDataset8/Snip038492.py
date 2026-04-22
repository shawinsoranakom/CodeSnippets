def _callMaybeAsync(self, func, *args, **kwargs):
        assert self._asyncioTestLoop is not None, "asyncio test loop is not initialized"
        ret = func(*args, **kwargs)
        if inspect.isawaitable(ret):
            fut = self._asyncioTestLoop.create_future()
            self._asyncioCallsQueue.put_nowait((fut, ret))
            return self._asyncioTestLoop.run_until_complete(fut)
        else:
            return ret