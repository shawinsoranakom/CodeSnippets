def pop(self) -> Request | None:
        while self.curprio is not None:
            try:
                q = self.queues[self.curprio]
            except KeyError:
                pass
            else:
                m = q.pop()
                if not q:
                    del self.queues[self.curprio]
                    q.close()
                    if not self._start_queues:
                        self._update_curprio()
                return m
            if self._start_queues:
                try:
                    q = self._start_queues[self.curprio]
                except KeyError:
                    self._update_curprio()
                else:
                    m = q.pop()
                    if not q:
                        del self._start_queues[self.curprio]
                        q.close()
                        self._update_curprio()
                    return m
            else:
                self._update_curprio()
        return None