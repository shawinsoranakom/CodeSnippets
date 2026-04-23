def _chrome_start(
            self,
            user_data_dir: str,
            touch_enabled: bool,
            headless=True,
            debug=False,
    ):
        headless_switches = {
            '--headless': '',
            '--disable-extensions': '',
            '--disable-background-networking' : '',
            '--disable-background-timer-throttling' : '',
            '--disable-backgrounding-occluded-windows': '',
            '--disable-renderer-backgrounding' : '',
            '--disable-breakpad': '',
            '--disable-client-side-phishing-detection': '',
            '--disable-crash-reporter': '',
            '--disable-dev-shm-usage': '',
            '--disable-namespace-sandbox': '',
            '--disable-translate': '',
            '--no-sandbox': '',
            '--disable-gpu': '',
            '--enable-unsafe-swiftshader': '',
            '--mute-audio': '',
        }
        switches = {
            # required for tours that use Youtube autoplay conditions (namely website_slides' "course_tour")
            '--autoplay-policy': 'no-user-gesture-required',
            '--disable-default-apps': '',
            '--disable-device-discovery-notifications': '',
            '--no-default-browser-check': '',
            '--remote-debugging-address': HOST,
            '--remote-debugging-port': str(self.remote_debugging_port),
            '--user-data-dir': user_data_dir,
            '--enable-logging': '',
            '--v': str(int(os.environ.get("ODOO_BROWSER_LOG_VERBOSITY", "0"))),
            '--no-first-run': '',
            # FIXME: these next 2 flags are temporarily uncommented to allow client
            # code to manually run garbage collection. This is done as currently
            # the Chrome unit test process doesn't have access to its available
            # memory, so it cannot run the GC efficiently and may run out of memory
            # and crash. These should be re-commented when the process is correctly
            # configured.
            '--enable-precise-memory-info': '',
            '--js-flags': '--expose-gc',
        }
        if headless:
            switches.update(headless_switches)
        if touch_enabled:
            # enable Chrome's Touch mode, useful to detect touch capabilities using
            # "'ontouchstart' in window"
            switches['--touch-events'] = ''
        if debug is not False:
            switches['--auto-open-devtools-for-tabs'] = ''
            switches['--start-fullscreen'] = ''

        cmd = [self.executable]
        cmd += ['%s=%s' % (k, v) if v else k for k, v in switches.items()]
        url = 'about:blank'
        cmd.append(url)
        try:
            proc, devtools_port = self._spawn_chrome(cmd)
        except OSError:
            raise unittest.SkipTest("%s not found" % cmd[0])
        self._logger.info('Chrome pid: %s', proc.pid)
        self._logger.info('Chrome headless temporary user profile dir: %s', self.user_data_dir)
        try:
            yield proc, devtools_port
        finally:
            self._logger.info("Terminating chrome headless with pid %s", proc.pid)
            main = psutil.Process(proc.pid)
            procs = [main] + main.children(recursive=True)
            proc.terminate()
            _, alive = psutil.wait_procs(procs, 5)
            if alive:  # can't early exit, it suppresses the finally'd exception if any
                self._logger.warning(
                    "Killing chrome descendants-or-self of %s: %d remaining%s",
                    proc.pid,
                    len(alive),
                    "".join(f"\n- {p.name()} ({p.status()})" for p in alive),
                )
                for p in alive:
                    p.kill()
                psutil.wait_procs(alive, 1)
                self.chrome_log_level = logging.RUNBOT