def process_limit(self):
        memory = memory_info(psutil.Process(os.getpid()))
        if config['limit_memory_soft'] and memory > config['limit_memory_soft']:
            _logger.warning('Server memory limit (%s) reached.', memory)
            self.limits_reached_threads.add(threading.current_thread())

        for thread in threading.enumerate():
            thread_type = getattr(thread, 'type', None)
            if not thread.daemon and thread_type != 'websocket' or thread_type == 'cron':
                # We apply the limits on cron threads and HTTP requests,
                # websocket requests excluded.
                if getattr(thread, 'start_time', None):
                    thread_execution_time = time.time() - thread.start_time
                    thread_limit_time_real = config['limit_time_real']
                    if (getattr(thread, 'type', None) == 'cron' and
                            config['limit_time_real_cron'] and config['limit_time_real_cron'] > 0):
                        thread_limit_time_real = config['limit_time_real_cron']
                    if thread_limit_time_real and thread_execution_time > thread_limit_time_real:
                        _logger.warning(
                            'Thread %s virtual real time limit (%d/%ds) reached.',
                            thread, thread_execution_time, thread_limit_time_real)
                        self.limits_reached_threads.add(thread)
        # Clean-up threads that are no longer alive
        # e.g. threads that exceeded their real time,
        # but which finished before the server could restart.
        for thread in list(self.limits_reached_threads):
            if not thread.is_alive():
                self.limits_reached_threads.remove(thread)
        if self.limits_reached_threads:
            self.limit_reached_time = self.limit_reached_time or time.time()
        else:
            self.limit_reached_time = None