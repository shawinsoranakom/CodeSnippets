def select(self, timeout=None):
            timeout = None if timeout is None else max(timeout, 0)
            # If max_ev is 0, kqueue will ignore the timeout. For consistent
            # behavior with the other selector classes, we prevent that here
            # (using max). See https://bugs.python.org/issue29255
            max_ev = self._max_events or 1
            ready = []
            try:
                kev_list = self._selector.control(None, max_ev, timeout)
            except InterruptedError:
                return ready

            fd_to_key_get = self._fd_to_key.get
            for kev in kev_list:
                fd = kev.ident
                flag = kev.filter
                key = fd_to_key_get(fd)
                if key:
                    events = ((flag == select.KQ_FILTER_READ and EVENT_READ)
                              | (flag == select.KQ_FILTER_WRITE and EVENT_WRITE))
                    ready.append((key, events & key.events))
            return ready