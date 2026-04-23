def process_signals(self):
        while self.queue:
            sig = self.queue.popleft()
            if sig in [signal.SIGINT, signal.SIGTERM]:
                raise KeyboardInterrupt
            elif sig == signal.SIGHUP:
                # restart on kill -HUP
                global server_phoenix  # noqa: PLW0603
                server_phoenix = True
                raise KeyboardInterrupt
            elif sig == signal.SIGQUIT:
                # dump stacks on kill -3
                dumpstacks()
            elif sig in [signal.SIGUSR1, signal.SIGUSR2]:
                # log ormcache stats on kill -SIGUSR1 or kill -SIGUSR2
                log_ormcache_stats(sig)
            elif sig == signal.SIGTTIN:
                # increase number of workers
                self.population += 1
            elif sig == signal.SIGTTOU:
                # decrease number of workers
                self.population -= 1