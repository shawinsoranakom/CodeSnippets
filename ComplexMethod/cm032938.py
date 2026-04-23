async def close(self) -> None:
        if self._close:
            return

        self._close = True

        while not self._queue.empty():
            try:
                _, _, result_queue = self._queue.get_nowait()
                try:
                    await result_queue.put(asyncio.CancelledError("Session is closing"))
                except Exception:
                    pass
            except asyncio.QueueEmpty:
                break
            except Exception:
                break

        try:
            self._event_loop.call_soon_threadsafe(self._event_loop.stop)
        except Exception:
            pass

        try:
            self._thread_pool.shutdown(wait=True)
        except Exception:
            pass

        self.__class__._ALL_INSTANCES.discard(self)