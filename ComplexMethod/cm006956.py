async def make_api_request(self) -> Data:
        """Make HTTP request with optimized parameter handling."""
        method = self.method
        url = self.url_input.strip() if isinstance(self.url_input, str) else ""
        headers = self.headers or {}
        body = self.body or {}
        timeout = self.timeout
        follow_redirects = self.follow_redirects
        save_to_file = self.save_to_file
        include_httpx_metadata = self.include_httpx_metadata

        # Security warning when redirects are enabled
        if follow_redirects:
            self.log(
                "Security Warning: HTTP redirects are enabled. This may allow SSRF bypass attacks "
                "where a public URL redirects to internal resources (e.g., cloud metadata endpoints). "
                "Only enable this if you trust the target server."
            )

        # if self.mode == "cURL" and self.curl_input:
        #     self._build_config = self.parse_curl(self.curl_input, dotdict())
        #     # After parsing curl, get the normalized URL
        #     url = self._build_config["url_input"]["value"]

        # Normalize URL before validation
        url = self._normalize_url(url)

        # Validate URL
        if not validators.url(url):
            msg = f"Invalid URL provided: {url}"
            raise ValueError(msg)

        # SSRF Protection: Validate URL to prevent access to internal resources
        # TODO: In next major version (2.0), remove warn_only=True to enforce blocking
        try:
            validate_url_for_ssrf(url, warn_only=True)
        except SSRFProtectionError as e:
            # This will only raise if SSRF protection is enabled and warn_only=False
            msg = f"SSRF Protection: {e}"
            raise ValueError(msg) from e

        # Process query parameters
        if isinstance(self.query_params, str):
            query_params = dict(parse_qsl(self.query_params))
        else:
            query_params = self.query_params.data if self.query_params else {}

        # Process headers and body
        headers = self._process_headers(headers)
        body = self._process_body(body)
        url = self.add_query_params(url, query_params)

        async with httpx.AsyncClient() as client:
            result = await self.make_request(
                client,
                method,
                url,
                headers,
                body,
                timeout,
                follow_redirects=follow_redirects,
                save_to_file=save_to_file,
                include_httpx_metadata=include_httpx_metadata,
            )
        self.status = result
        return result