def _wait_for_server(self, *, url: str, timeout: float):
        # run health check
        start = time.time()
        client = (
            httpx.Client(transport=httpx.HTTPTransport(uds=self.uds))
            if self.uds
            else requests
        )
        while True:
            try:
                if client.get(url).status_code == 200:
                    break
            except Exception:
                # this exception can only be raised by requests.get,
                # which means the server is not ready yet.
                # the stack trace is not useful, so we suppress it
                # by using `raise from None`.
                result = self._poll()
                if result is not None and result != 0:
                    raise RuntimeError("Server exited unexpectedly.") from None

                time.sleep(0.5)
                if time.time() - start > timeout:
                    raise RuntimeError("Server failed to start in time.") from None