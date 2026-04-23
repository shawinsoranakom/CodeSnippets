def run(self, preload=None, stop=False):
        """ Start the http server and the cron thread then wait for a signal.

        The first SIGINT or SIGTERM signal will initiate a graceful shutdown while
        a second one if any will force an immediate exit.
        """
        with Registry._lock:
            self.start(stop=stop)
            rc = preload_registries(preload)

        if stop:
            if config['test_enable']:
                from odoo.tests.result import _logger as logger  # noqa: PLC0415
                with Registry.registries._lock:
                    for db, registry in Registry.registries.items():
                        report = registry._assertion_report
                        log = logger.error if not report.wasSuccessful() \
                         else logger.warning if not report.testsRun \
                         else logger.info
                        log("%s when loading database %r", report, db)
            self.stop()
            return rc

        self.cron_spawn()

        # Wait for a first signal to be handled. (time.sleep will be interrupted
        # by the signal handler)
        try:
            while self.quit_signals_received == 0:
                self.process_limit()
                if self.limit_reached_time:
                    has_other_valid_requests = any(
                        not t.daemon and
                        t not in self.limits_reached_threads
                        for t in threading.enumerate()
                        if getattr(t, 'type', None) == 'http')
                    if (not has_other_valid_requests or
                            (time.time() - self.limit_reached_time) > SLEEP_INTERVAL):
                        # We wait there is no processing requests
                        # other than the ones exceeding the limits, up to 1 min,
                        # before asking for a reload.
                        _logger.info('Dumping stacktrace of limit exceeding threads before reloading')
                        dumpstacks(thread_idents=[thread.ident for thread in self.limits_reached_threads])
                        self.reload()
                        # `reload` increments `self.quit_signals_received`
                        # and the loop will end after this iteration,
                        # therefore leading to the server stop.
                        # `reload` also sets the `server_phoenix` flag
                        # to tell the server to restart the server after shutting down.
                    else:
                        time.sleep(1)
                else:
                    time.sleep(SLEEP_INTERVAL)
        except KeyboardInterrupt:
            pass

        self.stop()