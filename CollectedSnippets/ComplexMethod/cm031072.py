def close(self):
        if self._closed:
            return
        self._closed = True

        if self._w_out is not None:
            _close_file(self._w_out)
            self._w_out = None
        if self._w_err is not None:
            _close_file(self._w_err)
            self._w_err = None
        if self._w_exc is not None:
            _close_file(self._w_exc)
            self._w_exc = None

        self._capture()

        if self._rf_out is not None:
            _close_file(self._rf_out)
            self._rf_out = None
        if self._rf_err is not None:
            _close_file(self._rf_err)
            self._rf_err = None
        if self._rf_exc is not None:
            _close_file(self._rf_exc)
            self._rf_exc = None