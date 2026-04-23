async def acquire(self):
        """Acquire a lock.

        This method blocks until the lock is unlocked, then sets it to
        locked and returns True.
        """
        # Implement fair scheduling, where thread always waits
        # its turn. Jumping the queue if all are cancelled is an optimization.
        if (not self._locked and (self._waiters is None or
                all(w.cancelled() for w in self._waiters))):
            self._locked = True
            return True

        if self._waiters is None:
            self._waiters = collections.deque()
        fut = self._get_loop().create_future()
        self._waiters.append(fut)

        try:
            try:
                await fut
            finally:
                self._waiters.remove(fut)
        except exceptions.CancelledError:
            # Currently the only exception designed be able to occur here.

            # Ensure the lock invariant: If lock is not claimed (or about
            # to be claimed by us) and there is a Task in waiters,
            # ensure that the Task at the head will run.
            if not self._locked:
                self._wake_up_first()
            raise

        # assert self._locked is False
        self._locked = True
        return True