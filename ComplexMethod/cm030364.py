def _ensure_running_and_write(self, msg=None):
        with self._lock:
            if self._lock._recursion_count() > 1:
                # The code below is certainly not reentrant-safe, so bail out
                if msg is None:
                    raise self._reentrant_call_error()
                return self._reentrant_messages.append(msg)

            if self._fd is not None:
                # resource tracker was launched before, is it still running?
                if msg is None:
                    to_send = self._make_probe_message()
                else:
                    to_send = msg
                try:
                    self._write(to_send)
                except OSError:
                    self._teardown_dead_process()
                    self._launch()

                msg = None  # message was sent in probe
            else:
                self._launch()

        while True:
            try:
                reentrant_msg = self._reentrant_messages.popleft()
            except IndexError:
                break
            self._write(reentrant_msg)
        if msg is not None:
            self._write(msg)