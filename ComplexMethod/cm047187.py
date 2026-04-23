def stop(self):
        """ Shutdown the WSGI server. Wait for non daemon threads.
        """
        if server_phoenix:
            _logger.info("Initiating server reload")
        else:
            _logger.info("Initiating shutdown")
            _logger.info("Hit CTRL-C again or send a second signal to force the shutdown.")

        stop_time = time.time()

        if self.httpd:
            self.httpd.shutdown()

        super().stop()

        # Manually join() all threads before calling sys.exit() to allow a second signal
        # to trigger _force_quit() in case some non-daemon threads won't exit cleanly.
        # threading.Thread.join() should not mask signals (at least in python 2.5).
        me = threading.current_thread()
        _logger.debug('current thread: %r', me)
        for thread in threading.enumerate():
            _logger.debug('process %r (%r)', thread, thread.daemon)
            if (thread != me and not thread.daemon and thread.ident != self.main_thread_id and
                    thread not in self.limits_reached_threads):
                while thread.is_alive() and (time.time() - stop_time) < 1:
                    # We wait for requests to finish, up to 1 second.
                    _logger.debug('join and sleep')
                    # Need a busyloop here as thread.join() masks signals
                    # and would prevent the forced shutdown.
                    thread.join(0.05)
                    time.sleep(0.05)

        sql_db.close_all()

        current_process = psutil.Process()
        children = current_process.children(recursive=False)
        for child in children:
            _logger.info('A child process was found, pid is %s, process may hang', child)

        _logger.debug('--')
        logging.shutdown()