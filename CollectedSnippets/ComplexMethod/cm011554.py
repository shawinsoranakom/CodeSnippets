def start(self) -> None:
        """Start processes using parameters defined in the constructor."""
        if threading.current_thread() is threading.main_thread():
            # Register signal handlers for the signals specified in the environment variable
            signals_to_handle = os.environ.get(
                "TORCHELASTIC_SIGNALS_TO_HANDLE", "SIGTERM,SIGINT,SIGHUP,SIGQUIT"
            )
            signal_list = signals_to_handle.split(",")

            for sig_name in signal_list:
                try:
                    sig = getattr(signal, sig_name.strip())
                    signal.signal(sig, _terminate_process_handler)
                    logger.info("Registered signal handler for %s", sig_name)
                except (AttributeError, ValueError):
                    logger.warning(
                        "Failed to register signal handler for %s",
                        sig_name,
                        exc_info=True,
                    )
                except RuntimeError:
                    if IS_WINDOWS and sig_name.strip() in [
                        "SIGHUP",
                        "SIGQUIT",
                        "SIGUSR1",
                        "SIGUSR2",
                    ]:
                        logger.info(
                            "Signal %s is not supported on Windows, skipping", sig_name
                        )
                    else:
                        logger.warning(
                            "Failed to register signal handler for %s",
                            sig_name,
                            exc_info=True,
                        )
        else:
            logger.warning(
                "Failed to register signal handlers since torchelastic is running on a child thread. "
                "This could lead to orphaned worker processes if the torchrun is terminated."
            )
        self._start()
        for tail_log in self._tail_logs:
            tail_log.start()