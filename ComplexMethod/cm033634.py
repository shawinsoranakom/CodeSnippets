def request(self, method: str, url: str, data: t.Optional[str] = None, headers: t.Optional[dict[str, str]] = None) -> HttpResponse:
        """Perform an HTTP request and return the response."""
        if headers is None:
            headers = {}

        data_bytes = data.encode() if data else None

        request = urllib.request.Request(method=method, url=url, data=data_bytes, headers=headers)
        response: http.client.HTTPResponse

        display.info(f'HTTP {method} {url}', verbosity=2)

        attempts = 0
        max_attempts = 3
        sleep_seconds = 3

        status_code = 200
        reason = 'OK'
        body_bytes = b''

        while True:
            attempts += 1

            start = time.monotonic()

            if self.args.explain and not self.always:
                break

            try:
                try:
                    with urllib.request.urlopen(request) as response:
                        status_code = response.status
                        reason = response.reason
                        body_bytes = response.read()
                except urllib.error.HTTPError as ex:
                    status_code = ex.status
                    reason = ex.reason
                    body_bytes = ex.read()
            except Exception as ex:  # pylint: disable=broad-exception-caught
                if attempts >= max_attempts:
                    raise

                # all currently implemented methods are idempotent, so retries are unconditionally supported
                duration = time.monotonic() - start
                display.warning(f'{type(ex).__module__}.{type(ex).__name__}: {ex} [{duration:.2f} seconds]')
                time.sleep(sleep_seconds)

                continue

            break

        duration = time.monotonic() - start
        display.info(f'HTTP {method} {url} -> HTTP {status_code} ({reason}) [{len(body_bytes)} bytes, {duration:.2f} seconds]', verbosity=3)

        body = body_bytes.decode()

        return HttpResponse(method, url, status_code, body)