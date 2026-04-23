async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        assert self._state in (_State.ENTERED, _State.EXPIRING)

        if self._timeout_handler is not None:
            self._timeout_handler.cancel()
            self._timeout_handler = None

        if self._state is _State.EXPIRING:
            self._state = _State.EXPIRED

            if self._task.uncancel() <= self._cancelling and exc_type is not None:
                # Since there are no new cancel requests, we're
                # handling this.
                if issubclass(exc_type, exceptions.CancelledError):
                    raise TimeoutError from exc_val
                elif exc_val is not None:
                    self._insert_timeout_error(exc_val)
                    if isinstance(exc_val, ExceptionGroup):
                        for exc in exc_val.exceptions:
                            self._insert_timeout_error(exc)
        elif self._state is _State.ENTERED:
            self._state = _State.EXITED

        return None