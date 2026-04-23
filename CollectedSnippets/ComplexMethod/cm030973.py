def wrapper(self):
            size = wrapper.size
            memuse = wrapper.memuse
            if not real_max_memuse:
                maxsize = 5147
            else:
                maxsize = size

            if ((real_max_memuse or not dry_run)
                and real_max_memuse < maxsize * memuse):
                raise unittest.SkipTest(
                    "not enough memory: %.1fG minimum needed"
                    % (size * memuse / (1024 ** 3)))

            if real_max_memuse and verbose:
                print()
                print(" ... expected peak memory use: {peak:.1f}G"
                      .format(peak=size * memuse / (1024 ** 3)))
                watchdog = _MemoryWatchdog()
                watchdog.start()
            else:
                watchdog = None

            try:
                return f(self, maxsize)
            finally:
                if watchdog:
                    watchdog.stop()