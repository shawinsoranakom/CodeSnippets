def browser_js(self, url_path, code, ready='', login=None, timeout=60, cookies=None, error_checker=None, watch=False, success_signal=DEFAULT_SUCCESS_SIGNAL, debug=False, cpu_throttling=None, **kw):
        """ Test JavaScript code running in the browser.

        To signal success test do: `console.log()` with the expected `success_signal`. Default is "test successful"
        To signal test failure raise an exception or call `console.error` with a message.
        Test will stop when a failure occurs if `error_checker` is not defined or returns `True` for this message

        :param string url_path: URL path to load the browser page on
        :param string code: JavaScript code to be executed
        :param string ready: JavaScript object to wait for before proceeding with the test
        :param string login: logged in user which will execute the test. e.g. 'admin', 'demo'
        :param int timeout: maximum time to wait for the test to complete (in seconds). Default is 60 seconds
        :param dict cookies: dictionary of cookies to set before loading the page
        :param error_checker: function to filter failures out.
            If provided, the function is called with the error log message, and if it returns `False` the log is ignored and the test continue
            If not provided, every error log triggers a failure
        :param bool watch: open a new browser window to watch the test execution
        :param string success_signal: string signal to wait for to consider the test successful
        :param bool debug: automatically open a fullscreen Chrome window with opened devtools and a debugger breakpoint set at the start of the tour.
            The tour is ran with the `debug=assets` query parameter. When an error is thrown, the debugger stops on the exception.
        :param int cpu_throttling: CPU throttling rate as a slowdown factor (1 is no throttle, 2 is 2x slowdown, etc)
        """
        if not self.env.registry.loaded:
            self._logger.warning('HttpCase test should be in post_install only')

        # increase timeout if coverage is running
        if any(f.filename.endswith('/coverage/execfile.py') for f in inspect.stack()  if f.filename):
            timeout = timeout * 1.5

        if debug is not False:
            watch = True
            timeout = 1e6
        if watch:
            self._logger.warning('watch mode is only suitable for local testing')

        browser = ChromeBrowser(self, headless=not watch, success_signal=success_signal, debug=debug)
        with self.allow_requests(browser=browser), contextlib.ExitStack() as atexit:
            atexit.callback(self._wait_remaining_requests)
            atexit.enter_context(browser.cleanup)
            if "bus.bus" in self.env.registry:
                from odoo.addons.bus.websocket import CloseCode, _kick_all, WebsocketConnectionHandler  # noqa: PLC0415
                from odoo.addons.bus.models.bus import BusBus  # noqa: PLC0415

                atexit.callback(_kick_all, CloseCode.KILL_NOW)
                original_send_one = BusBus._sendone

                def sendone_wrapper(self, target, notification_type, message):
                    original_send_one(self, target, notification_type, message)
                    self.env.cr.precommit.run()  # Trigger the creation of bus.bus records
                    self.env.cr.postcommit.run()  # Trigger notification dispatching

                atexit.enter_context(patch.object(BusBus, "_sendone", sendone_wrapper))
                atexit.enter_context(patch.object(
                    WebsocketConnectionHandler, "websocket_allowed", return_value=True
                ))

            self.authenticate(login, login, browser=browser)
            # Flush and clear the current transaction.  This is useful in case
            # we make requests to the server, as these requests are made with
            # test cursors, which uses different caches than this transaction.
            self.cr.flush()
            self.cr.clear()
            url = urljoin(self.base_url(), url_path)
            if watch:
                parsed = urlsplit(url)
                qs = dict(parse_qsl(parsed.query))
                qs['watch'] = '1'
                if debug is not False:
                    qs['debug'] = "assets"
                url = urlunsplit(parsed._replace(query=urlencode(qs)))
            self._logger.info('Open "%s" in browser', url)

            browser.screencaster.start()
            if cookies:
                for name, value in cookies.items():
                    browser.set_cookie(name, value, '/', HOST)

            cpu_throttling_os = os.environ.get('ODOO_BROWSER_CPU_THROTTLING')  # used by dedicated runbot builds
            cpu_throttling = int(cpu_throttling_os) if cpu_throttling_os else cpu_throttling

            if cpu_throttling:
                _logger.log(
                    logging.INFO if cpu_throttling_os else logging.WARNING,
                    'CPU throttling mode is only suitable for local testing - '
                    'Throttling browser CPU to %sx slowdown and extending timeout to %s sec', cpu_throttling, timeout)
                browser.throttle(cpu_throttling)

            browser.navigate_to(url, wait_stop=not bool(ready))

            # Needed because tests like test01.js (qunit tests) are passing a ready
            # code = ""
            self.assertTrue(browser._wait_ready(ready), 'The ready "%s" code was always falsy' % ready)

            error = False
            try:
                browser._wait_code_ok(code, timeout, error_checker=error_checker)
            except ChromeBrowserException as chrome_browser_exception:
                error = chrome_browser_exception
            if error:  # dont keep initial traceback, keep that outside of except
                if code:
                    message = 'The test code "%s" failed' % code
                else:
                    message = "Some js test failed"
                self.fail('%s\n\n%s' % (message, error))