def enqueue(self, msg: ForwardMsg) -> None:
        self._browser_queue.enqueue(msg)