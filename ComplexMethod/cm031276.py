def _try_finish(self):
        assert not self._finished
        if self._returncode is None:
            return
        if not self._pipes_connected:
            # self._pipes_connected can be False if not all pipes were connected
            # because either the process failed to start or the self._connect_pipes task
            # got cancelled. In this broken state we consider all pipes disconnected and
            # to avoid hanging forever in self._wait as otherwise _exit_waiters
            # would never be woken up, we wake them up here.
            for waiter in self._exit_waiters:
                if not waiter.done():
                    waiter.set_result(self._returncode)
        if all(p is not None and p.disconnected
               for p in self._pipes.values()):
            self._finished = True
            self._call(self._call_connection_lost, None)