def add_signal_handler(self, sig, callback, *args):
        """Add a handler for a signal.  UNIX only.

        Raise ValueError if the signal number is invalid or uncatchable.
        Raise RuntimeError if there is a problem setting up the handler.
        """
        if (coroutines.iscoroutine(callback) or
                coroutines._iscoroutinefunction(callback)):
            raise TypeError("coroutines cannot be used "
                            "with add_signal_handler()")
        self._check_signal(sig)
        self._check_closed()
        try:
            # set_wakeup_fd() raises ValueError if this is not the
            # main thread.  By calling it early we ensure that an
            # event loop running in another thread cannot add a signal
            # handler.
            signal.set_wakeup_fd(self._csock.fileno())
        except (ValueError, OSError) as exc:
            raise RuntimeError(str(exc))

        handle = events.Handle(callback, args, self, None)
        self._signal_handlers[sig] = handle

        try:
            # Register a dummy signal handler to ask Python to write the signal
            # number in the wakeup file descriptor. _process_self_data() will
            # read signal numbers from this file descriptor to handle signals.
            signal.signal(sig, _sighandler_noop)

            # Set SA_RESTART to limit EINTR occurrences.
            signal.siginterrupt(sig, False)
        except OSError as exc:
            del self._signal_handlers[sig]
            if not self._signal_handlers:
                try:
                    signal.set_wakeup_fd(-1)
                except (ValueError, OSError) as nexc:
                    logger.info('set_wakeup_fd(-1) failed: %s', nexc)

            if exc.errno == errno.EINVAL:
                raise RuntimeError(f'sig {sig} cannot be caught')
            else:
                raise