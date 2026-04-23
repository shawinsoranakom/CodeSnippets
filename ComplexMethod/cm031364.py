def get_event(self, block: bool = True) -> Event | None:
        """
        Get an event from the console event queue.

        Parameters:
        - block (bool): Whether to block until an event is available.

        Returns:
        - Event: Event object from the event queue.
        """
        if not block and not self.wait(timeout=0):
            return None

        while self.event_queue.empty():
            while True:
                try:
                    self.push_char(self.__read(1))
                except OSError as err:
                    if err.errno == errno.EINTR:
                        if not self.event_queue.empty():
                            return self.event_queue.get()
                        else:
                            continue
                    elif err.errno == errno.EIO:
                        raise SystemExit(errno.EIO)
                    else:
                        raise
                else:
                    break
        return self.event_queue.get()