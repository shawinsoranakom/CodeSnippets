def _wait_ready(self, ready_code=None, timeout=60):
        timeout *= self.throttling_factor
        ready_code = ready_code or "document.readyState === 'complete'"
        self._logger.info('Evaluate ready code "%s"', ready_code)
        start_time = time.time()
        result = None
        while True:
            taken = time.time() - start_time
            if taken > timeout:
                break

            try:
                result = self._websocket_request('Runtime.evaluate', params={
                    'expression': "try { %s } catch {}" % ready_code,
                    'awaitPromise': True,
                }, timeout=timeout-taken)['result']
            except CancelledError:
                exc = self._result.done() and self._result.exception()
                if exc:
                    raise exc from None
                result = "cancelled"

            if result == {'type': 'boolean', 'value': True}:
                time_to_ready = time.time() - start_time
                if taken > 2:
                    self._logger.info('The ready code tooks too much time : %s', time_to_ready)
                return True

        exc = self._result.done() and self._result.exception()
        if exc:
            raise exc from None
        self.take_screenshot(prefix='sc_failed_ready_')
        self._logger.info('Ready code last try result: %s', result)
        return False