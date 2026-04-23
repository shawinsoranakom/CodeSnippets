def _clear_dead_receivers(self):
        # Note: caller is assumed to hold self.lock.
        if self._dead_receivers:
            self._dead_receivers = False
            self.receivers = [
                r
                for r in self.receivers
                if (
                    not (isinstance(r[1], weakref.ReferenceType) and r[1]() is None)
                    and not (r[2] is not None and r[2]() is None)
                )
            ]