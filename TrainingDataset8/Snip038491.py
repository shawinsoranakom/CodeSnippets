def _callAsync(self, func, *args, **kwargs):
        assert self._asyncioTestLoop is not None, "asyncio test loop is not initialized"
        ret = func(*args, **kwargs)
        assert inspect.isawaitable(ret), f"{func!r} returned non-awaitable"
        fut = self._asyncioTestLoop.create_future()
        self._asyncioCallsQueue.put_nowait((fut, ret))
        return self._asyncioTestLoop.run_until_complete(fut)