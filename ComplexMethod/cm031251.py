async def _aexit(self, et, exc):
        self._exiting = True

        if (exc is not None and
                self._is_base_error(exc) and
                self._base_error is None):
            self._base_error = exc

        if et is not None and issubclass(et, exceptions.CancelledError):
            propagate_cancellation_error = exc
        else:
            propagate_cancellation_error = None

        if et is not None:
            if not self._aborting:
                # Our parent task is being cancelled:
                #
                #    async with TaskGroup() as g:
                #        g.create_task(...)
                #        await ...  # <- CancelledError
                #
                # or there's an exception in "async with":
                #
                #    async with TaskGroup() as g:
                #        g.create_task(...)
                #        1 / 0
                #
                self._abort()

        # We use while-loop here because "self._on_completed_fut"
        # can be cancelled multiple times if our parent task
        # is being cancelled repeatedly (or even once, when
        # our own cancellation is already in progress)
        while self._tasks:
            if self._on_completed_fut is None:
                self._on_completed_fut = self._loop.create_future()

            try:
                await self._on_completed_fut
            except exceptions.CancelledError as ex:
                if not self._aborting:
                    # Our parent task is being cancelled:
                    #
                    #    async def wrapper():
                    #        async with TaskGroup() as g:
                    #            g.create_task(foo)
                    #
                    # "wrapper" is being cancelled while "foo" is
                    # still running.
                    propagate_cancellation_error = ex
                    self._abort()

            self._on_completed_fut = None

        assert not self._tasks

        if self._base_error is not None:
            try:
                raise self._base_error
            finally:
                exc = None

        if self._parent_cancel_requested:
            # If this flag is set we *must* call uncancel().
            if self._parent_task.uncancel() == 0:
                # If there are no pending cancellations left,
                # don't propagate CancelledError.
                propagate_cancellation_error = None

        # Propagate CancelledError if there is one, except if there
        # are other errors -- those have priority.
        try:
            if propagate_cancellation_error is not None and not self._errors:
                try:
                    raise propagate_cancellation_error
                finally:
                    exc = None
        finally:
            propagate_cancellation_error = None

        if et is not None and not issubclass(et, exceptions.CancelledError):
            self._errors.append(exc)

        if self._errors:
            # If the parent task is being cancelled from the outside
            # of the taskgroup, un-cancel and re-cancel the parent task,
            # which will keep the cancel count stable.
            if self._parent_task.cancelling():
                self._parent_task.uncancel()
                self._parent_task.cancel()
            try:
                raise BaseExceptionGroup(
                    'unhandled errors in a TaskGroup',
                    self._errors,
                ) from None
            finally:
                exc = None