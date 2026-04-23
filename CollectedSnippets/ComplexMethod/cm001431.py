def _make_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | str | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request and return a structured response.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: The URL to request
            headers: Optional headers
            params: Optional query parameters
            body: Optional request body
            timeout: Optional timeout override

        Returns:
            dict: Structured response with status, headers, and body
        """
        if not self._is_domain_allowed(url):
            raise HTTPError(
                f"Domain not in allowed list. Allowed: {self.config.allowed_domains}",
                url=url,
            )

        request_timeout = timeout or self.config.default_timeout
        request_headers = headers or {}

        try:
            if method == "GET":
                response = self.session.get(
                    url, headers=request_headers, params=params, timeout=request_timeout
                )
            elif method == "POST":
                response = self.session.post(
                    url,
                    headers=request_headers,
                    params=params,
                    json=body if isinstance(body, dict) else None,
                    data=body if isinstance(body, str) else None,
                    timeout=request_timeout,
                )
            elif method == "PUT":
                response = self.session.put(
                    url,
                    headers=request_headers,
                    params=params,
                    json=body if isinstance(body, dict) else None,
                    data=body if isinstance(body, str) else None,
                    timeout=request_timeout,
                )
            elif method == "DELETE":
                response = self.session.delete(
                    url, headers=request_headers, params=params, timeout=request_timeout
                )
            else:
                raise HTTPError(f"Unsupported HTTP method: {method}", url=url)

            # Check response size
            content_length = len(response.content)
            if content_length > self.config.max_response_size:
                raise HTTPError(
                    f"Response too large: {content_length} bytes "
                    f"(max: {self.config.max_response_size})",
                    status_code=response.status_code,
                    url=url,
                )

            # Try to parse as JSON, fall back to text
            try:
                response_body = response.json()
            except json.JSONDecodeError:
                response_body = response.text

            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response_body,
                "url": response.url,
            }

        except requests.exceptions.Timeout:
            raise HTTPError(
                f"Request timed out after {request_timeout} seconds", url=url
            )
        except requests.exceptions.ConnectionError as e:
            raise HTTPError(f"Connection error: {e}", url=url)
        except requests.exceptions.RequestException as e:
            raise HTTPError(f"Request failed: {e}", url=url)