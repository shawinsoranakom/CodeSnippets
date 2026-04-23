def call_exception_handler(self, context):
        """Call the current event loop's exception handler.

        The context argument is a dict containing the following keys:

        - 'message': Error message;
        - 'exception' (optional): Exception object;
        - 'future' (optional): Future instance;
        - 'task' (optional): Task instance;
        - 'handle' (optional): Handle instance;
        - 'protocol' (optional): Protocol instance;
        - 'transport' (optional): Transport instance;
        - 'socket' (optional): Socket instance;
        - 'source_traceback' (optional): Traceback of the source;
        - 'handle_traceback' (optional): Traceback of the handle;
        - 'asyncgen' (optional): Asynchronous generator that caused
                                 the exception.

        New keys maybe introduced in the future.

        Note: do not overload this method in an event loop subclass.
        For custom exception handling, use the
        `set_exception_handler()` method.
        """
        if self._exception_handler is None:
            try:
                self.default_exception_handler(context)
            except (SystemExit, KeyboardInterrupt):
                raise
            except BaseException:
                # Second protection layer for unexpected errors
                # in the default implementation, as well as for subclassed
                # event loops with overloaded "default_exception_handler".
                logger.error('Exception in default exception handler',
                             exc_info=True)
        else:
            try:
                ctx = None
                thing = context.get("task")
                if thing is None:
                    # Even though Futures don't have a context,
                    # Task is a subclass of Future,
                    # and sometimes the 'future' key holds a Task.
                    thing = context.get("future")
                if thing is None:
                    # Handles also have a context.
                    thing = context.get("handle")
                if thing is not None and hasattr(thing, "get_context"):
                    ctx = thing.get_context()
                if ctx is not None and hasattr(ctx, "run"):
                    ctx.run(self._exception_handler, self, context)
                else:
                    self._exception_handler(self, context)
            except (SystemExit, KeyboardInterrupt):
                raise
            except BaseException as exc:
                # Exception in the user set custom exception handler.
                try:
                    # Let's try default handler.
                    self.default_exception_handler({
                        'message': 'Unhandled error in exception handler',
                        'exception': exc,
                        'context': context,
                    })
                except (SystemExit, KeyboardInterrupt):
                    raise
                except BaseException:
                    # Guard 'default_exception_handler' in case it is
                    # overloaded.
                    logger.error('Exception in default exception handler '
                                 'while handling an unexpected error '
                                 'in custom exception handler',
                                 exc_info=True)