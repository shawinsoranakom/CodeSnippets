async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[dict] = None,
        files: list[tuple[str, tuple[str, BytesIO, str]]] | None = None,
        data: Any | None = None,
        json: Any | None = None,
        allow_redirects: bool = True,
        max_redirects: int = 10,
        **kwargs,
    ) -> Response:
        # Convert auth tuple to aiohttp.BasicAuth if necessary
        if "auth" in kwargs and isinstance(kwargs["auth"], tuple):
            kwargs["auth"] = aiohttp.BasicAuth(*kwargs["auth"])

        if files is not None:
            if json is not None:
                raise ValueError(
                    "Cannot mix file uploads with JSON body; "
                    "use 'data' for extra form fields instead."
                )

            form = FormData(quote_fields=False)
            # add normal form fields first
            if isinstance(data, dict):
                for k, v in data.items():
                    form.add_field(k, str(v))
            elif data is not None:
                raise ValueError(
                    "When uploading files, 'data' must be a dict of form fields."
                )

            # add the file parts
            for field_name, (filename, fh, content_type) in files:
                form.add_field(
                    name=field_name,
                    value=fh,
                    filename=filename,
                    content_type=content_type or "application/octet-stream",
                )

            data = form

        # Validate URL and get trust status
        parsed_url, is_trusted, ip_addresses = await validate_url_host(
            url, self.trusted_origins
        )

        # Apply any extra user-defined validation/transformation
        if self.extra_url_validator is not None:
            parsed_url = self.extra_url_validator(parsed_url)

        # Pin the URL if untrusted
        hostname = parsed_url.hostname
        if hostname is None:
            raise ValueError(f"Invalid URL: Unable to determine hostname of {url}")

        original_url = parsed_url.geturl()
        connector: Optional[aiohttp.TCPConnector] = None
        if not is_trusted:
            # Replace hostname with IP for connection but preserve SNI via resolver
            resolver = HostResolver(ssl_hostname=hostname, ip_addresses=ip_addresses)
            ssl_context = ssl.create_default_context()
            connector = aiohttp.TCPConnector(resolver=resolver, ssl=ssl_context)
        session_kwargs: dict = {}
        if connector:
            session_kwargs["connector"] = connector

        # Merge any extra headers
        req_headers = dict(headers) if headers else {}
        if self.extra_headers is not None:
            req_headers.update(self.extra_headers)

        # Set default User-Agent if not provided
        if "User-Agent" not in req_headers and "user-agent" not in req_headers:
            req_headers["User-Agent"] = DEFAULT_USER_AGENT

        # Override Host header if using IP connection
        if connector:
            req_headers["Host"] = hostname

        # Override data if files are provided
        # Set max_field_size to handle servers with large headers (e.g., long CSP headers)
        # Default is 8190 bytes, we increase to 16KB to accommodate legitimate large headers
        session_kwargs["max_field_size"] = 16384

        async with aiohttp.ClientSession(**session_kwargs) as session:
            # Perform the request with redirects disabled for manual handling
            async with session.request(
                method,
                parsed_url.geturl(),
                headers=req_headers,
                allow_redirects=False,
                data=data,
                json=json,
                **kwargs,
            ) as response:
                if self.raise_for_status:
                    try:
                        response.raise_for_status()
                    except ClientResponseError as e:
                        body = await response.read()
                        error_message = f"HTTP {response.status} Error: {response.reason}, Body: {body.decode(errors='replace')}"

                        # Raise specific exceptions based on status code range
                        if 400 <= response.status <= 499:
                            raise HTTPClientError(error_message, response.status) from e
                        elif 500 <= response.status <= 599:
                            raise HTTPServerError(error_message, response.status) from e
                        else:
                            # Generic fallback for other HTTP errors
                            raise Exception(error_message) from e

                # If allowed and a redirect is received, follow the redirect manually
                if allow_redirects and response.status in (301, 302, 303, 307, 308):
                    if max_redirects <= 0:
                        raise Exception("Too many redirects.")

                    location = response.headers.get("Location")
                    if not location:
                        return Response(
                            response=response,
                            url=original_url,
                            body=await response.read(),
                        )

                    # The base URL is the pinned_url we just used
                    # so that relative redirects resolve correctly.
                    redirect_url = urlparse(urljoin(parsed_url.geturl(), location))
                    # Carry forward the same headers but update Host
                    new_headers = _remove_insecure_headers(
                        req_headers, parsed_url, redirect_url
                    )

                    return await self.request(
                        method,
                        redirect_url.geturl(),
                        headers=new_headers,
                        allow_redirects=allow_redirects,
                        max_redirects=max_redirects - 1,
                        files=files,
                        data=data,
                        json=json,
                        **kwargs,
                    )

                # Reset response URL to original host for clarity
                if parsed_url.hostname != hostname:
                    try:
                        response.url = original_url  # type: ignore
                    except Exception:
                        pass

                return Response(
                    response=response,
                    url=original_url,
                    body=await response.read(),
                )