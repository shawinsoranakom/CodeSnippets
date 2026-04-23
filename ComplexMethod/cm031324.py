def run(self, coro, *, context=None):
        """Run code in the embedded event loop."""
        if events._get_running_loop() is not None:
            # fail fast with short traceback
            raise RuntimeError(
                "Runner.run() cannot be called from a running event loop")

        self._lazy_init()

        if not coroutines.iscoroutine(coro):
            if inspect.isawaitable(coro):
                async def _wrap_awaitable(awaitable):
                    return await awaitable

                coro = _wrap_awaitable(coro)
            else:
                raise TypeError('An asyncio.Future, a coroutine or an '
                                'awaitable is required')

        if context is None:
            context = self._context

        task = self._loop.create_task(coro, context=context)

        if (threading.current_thread() is threading.main_thread()
            and signal.getsignal(signal.SIGINT) is signal.default_int_handler
        ):
            sigint_handler = functools.partial(self._on_sigint, main_task=task)
            try:
                signal.signal(signal.SIGINT, sigint_handler)
            except ValueError:
                # `signal.signal` may throw if `threading.main_thread` does
                # not support signals (e.g. embedded interpreter with signals
                # not registered - see gh-91880)
                sigint_handler = None
        else:
            sigint_handler = None

        self._interrupt_count = 0
        try:
            return self._loop.run_until_complete(task)
        except exceptions.CancelledError:
            if self._interrupt_count > 0:
                uncancel = getattr(task, "uncancel", None)
                if uncancel is not None and uncancel() == 0:
                    raise KeyboardInterrupt()
            raise  # CancelledError
        finally:
            if (sigint_handler is not None
                and signal.getsignal(signal.SIGINT) is sigint_handler
            ):
                signal.signal(signal.SIGINT, signal.default_int_handler)