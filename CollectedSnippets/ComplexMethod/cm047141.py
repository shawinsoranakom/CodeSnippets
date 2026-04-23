def _wait_code_ok(self, code, timeout, error_checker=None):
        timeout *= self.throttling_factor
        self.error_checker = error_checker
        self._logger.info('Evaluate test code "%s"', code)
        start = time.time()
        res = self._websocket_request('Runtime.evaluate', params={
            'expression': code,
            'awaitPromise': True,
        }, timeout=timeout)['result']
        if res.get('subtype') == 'error':
            raise ChromeBrowserException("Running code returned an error: %s" % res)

        err = ChromeBrowserException("failed")
        try:
            # if the runcode was a promise which took some time to execute,
            # discount that from the timeout
            if self._result.result(time.time() - start + timeout) and not self.had_failure:
                self.chrome_log_level = logging.INFO
                return
        except CancelledError:
            # regular-ish shutdown
            self.chrome_log_level = logging.INFO
            return
        except ChromeBrowserException:
            self.screencaster.save()
            raise
        except Exception as e:
            err = e

        self.take_screenshot()
        self.screencaster.save()

        if isinstance(err, concurrent.futures.TimeoutError):
            raise ChromeBrowserException('Script timeout exceeded') from err
        raise ChromeBrowserException("Unknown error") from err