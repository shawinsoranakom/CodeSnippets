async def __aexit__(self, *exc_details):
        exc = exc_details[1]
        received_exc = exc is not None

        # We manipulate the exception state so it behaves as though
        # we were actually nesting multiple with statements
        frame_exc = sys.exception()
        def _fix_exception_context(new_exc, old_exc):
            # Context may not be correct, so find the end of the chain
            while 1:
                exc_context = new_exc.__context__
                if exc_context is None or exc_context is old_exc:
                    # Context is already set correctly (see issue 20317)
                    return
                if exc_context is frame_exc:
                    break
                new_exc = exc_context
            # Change the end of the chain to point to the exception
            # we expect it to reference
            new_exc.__context__ = old_exc

        # Callbacks are invoked in LIFO order to match the behaviour of
        # nested context managers
        suppressed_exc = False
        pending_raise = False
        while self._exit_callbacks:
            is_sync, cb = self._exit_callbacks.pop()
            try:
                if exc is None:
                    exc_details = None, None, None
                else:
                    exc_details = type(exc), exc, exc.__traceback__
                if is_sync:
                    cb_suppress = cb(*exc_details)
                else:
                    cb_suppress = await cb(*exc_details)

                if cb_suppress:
                    suppressed_exc = True
                    pending_raise = False
                    exc = None
            except BaseException as new_exc:
                # simulate the stack of exceptions by setting the context
                _fix_exception_context(new_exc, exc)
                pending_raise = True
                exc = new_exc

        if pending_raise:
            try:
                # bare "raise exc" replaces our carefully
                # set-up context
                fixed_ctx = exc.__context__
                raise exc
            except BaseException:
                exc.__context__ = fixed_ctx
                raise
        return received_exc and suppressed_exc