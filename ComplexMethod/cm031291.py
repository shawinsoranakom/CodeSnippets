def _loop_reading(self, fut=None):
        length = -1
        data = None
        try:
            if fut is not None:
                assert self._read_fut is fut or (self._read_fut is None and
                                                 self._closing)
                self._read_fut = None
                if fut.done():
                    # deliver data later in "finally" clause
                    length = fut.result()
                    if length == 0:
                        # we got end-of-file so no need to reschedule a new read
                        return

                    # It's a new slice so make it immutable so protocols upstream don't have problems
                    data = bytes(memoryview(self._data)[:length])
                else:
                    # the future will be replaced by next proactor.recv call
                    fut.cancel()

            if self._closing:
                # since close() has been called we ignore any read data
                return

            # bpo-33694: buffer_updated() has currently no fast path because of
            # a data loss issue caused by overlapped WSASend() cancellation.

            if not self._paused:
                # reschedule a new read
                self._read_fut = self._loop._proactor.recv_into(self._sock, self._data)
        except ConnectionAbortedError as exc:
            if not self._closing:
                self._fatal_error(exc, 'Fatal read error on pipe transport')
            elif self._loop.get_debug():
                logger.debug("Read error on pipe transport while closing",
                             exc_info=True)
        except ConnectionResetError as exc:
            self._force_close(exc)
        except OSError as exc:
            self._fatal_error(exc, 'Fatal read error on pipe transport')
        except exceptions.CancelledError:
            if not self._closing:
                raise
        else:
            if not self._paused:
                self._read_fut.add_done_callback(self._loop_reading)
        finally:
            if length > -1:
                self._data_received(data, length)