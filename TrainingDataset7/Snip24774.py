def __del__(self):
        try:
            self._unawaited_coroutine.close()
        except AttributeError:
            # View was never called.
            pass