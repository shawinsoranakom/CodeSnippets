def send(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        data: Any | None = None,
        stream: bool = False,
    ) -> requests.Response:
        import requests

        headers = headers or {}
        if "User-Agent" not in headers:
            headers["User-Agent"] = f"pathway/{pw.__version__}"
        retry_policy = self._retry_policy
        for n_attempt in range(0, self._n_retries + 1):
            try:
                response = requests.request(
                    self._request_method,
                    url,
                    timeout=self._timeout,
                    headers=headers,
                    data=data,
                    allow_redirects=self._allow_redirects,
                    stream=stream,
                )
                if response.ok or response.status_code not in self._retry_codes:
                    break
            except requests.exceptions.ConnectTimeout:
                if n_attempt == self._n_retries:
                    raise

            sleep_duration = retry_policy.wait_duration_before_retry()
            time.sleep(sleep_duration)

        return response