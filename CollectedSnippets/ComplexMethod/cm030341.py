def _set(self, i, success_result):
        self._number_left -= 1
        success, result = success_result
        if success and self._success:
            self._value[i*self._chunksize:(i+1)*self._chunksize] = result
            if self._number_left == 0:
                if self._callback:
                    self._callback(self._value)
                del self._cache[self._job]
                self._event.set()
                self._pool = None
        else:
            if not success and self._success:
                # only store first exception
                self._success = False
                self._value = result
            if self._number_left == 0:
                # only consider the result ready once all jobs are done
                if self._error_callback:
                    self._error_callback(self._value)
                del self._cache[self._job]
                self._event.set()
                self._pool = None