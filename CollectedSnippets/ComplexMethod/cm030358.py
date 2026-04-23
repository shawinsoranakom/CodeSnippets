def _send_bytes(self, buf):
            if self._send_ov is not None:
                # A connection should only be used by a single thread
                raise ValueError("concurrent send_bytes() calls "
                                 "are not supported")
            ov, err = _winapi.WriteFile(self._handle, buf, overlapped=True)
            self._send_ov = ov
            try:
                if err == _winapi.ERROR_IO_PENDING:
                    waitres = _winapi.WaitForMultipleObjects(
                        [ov.event], False, INFINITE)
                    assert waitres == WAIT_OBJECT_0
            except:
                ov.cancel()
                raise
            finally:
                self._send_ov = None
                nwritten, err = ov.GetOverlappedResult(True)
            if err == _winapi.ERROR_OPERATION_ABORTED:
                # close() was called by another thread while
                # WaitForMultipleObjects() was waiting for the overlapped
                # operation.
                raise OSError(errno.EPIPE, "handle is closed")
            assert err == 0
            assert nwritten == len(buf)