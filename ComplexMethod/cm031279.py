async def get(self):
        """Remove and return an item from the queue.

        If queue is empty, wait until an item is available.

        Raises QueueShutDown if the queue has been shut down and is empty, or
        if the queue has been shut down immediately.
        """
        while self.empty():
            if self._is_shutdown and self.empty():
                raise QueueShutDown
            getter = self._get_loop().create_future()
            self._getters.append(getter)
            try:
                await getter
            except:
                getter.cancel()  # Just in case getter is not done yet.
                try:
                    # Clean self._getters from canceled getters.
                    self._getters.remove(getter)
                except ValueError:
                    # The getter could be removed from self._getters by a
                    # previous put_nowait call, or a shutdown call.
                    pass
                if not self.empty() and not getter.cancelled():
                    # We were woken up by put_nowait(), but can't take
                    # the call.  Wake up the next in line.
                    self._wakeup_next(self._getters)
                raise
        return self.get_nowait()