def select(self, timeout=None):
        # This is shared between poll() and epoll().
        # epoll() has a different signature and handling of timeout parameter.
        if timeout is None:
            timeout = None
        elif timeout <= 0:
            timeout = 0
        else:
            # poll() has a resolution of 1 millisecond, round away from
            # zero to wait *at least* timeout seconds.
            timeout = math.ceil(timeout * 1e3)
        ready = []
        try:
            fd_event_list = self._selector.poll(timeout)
        except InterruptedError:
            return ready

        fd_to_key_get = self._fd_to_key.get
        for fd, event in fd_event_list:
            key = fd_to_key_get(fd)
            if key:
                events = ((event & ~self._EVENT_READ and EVENT_WRITE)
                           | (event & ~self._EVENT_WRITE and EVENT_READ))
                ready.append((key, events & key.events))
        return ready