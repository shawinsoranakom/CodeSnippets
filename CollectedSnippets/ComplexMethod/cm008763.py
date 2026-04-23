def _send(self, request: Request):
        max_redirects_exceeded = False
        session: curl_cffi.requests.Session = self._get_instance(
            cookiejar=self._get_cookiejar(request) if 'cookie' not in request.headers else None)

        if self.verbose:
            session.curl.setopt(CurlOpt.VERBOSE, 1)

        proxies = self._get_proxies(request)
        if 'no' in proxies:
            session.curl.setopt(CurlOpt.NOPROXY, proxies['no'])
            proxies.pop('no', None)

        # curl doesn't support per protocol proxies, so we select the one that matches the request protocol
        proxy = select_proxy(request.url, proxies=proxies)
        if proxy:
            session.curl.setopt(CurlOpt.PROXY, proxy)
            scheme = urllib.parse.urlparse(request.url).scheme.lower()
            if scheme != 'http':
                # Enable HTTP CONNECT for HTTPS urls.
                # Don't use CONNECT for http for compatibility with urllib behaviour.
                # See: https://curl.se/libcurl/c/CURLOPT_HTTPPROXYTUNNEL.html
                session.curl.setopt(CurlOpt.HTTPPROXYTUNNEL, 1)

            # curl_cffi does not currently set these for proxies
            session.curl.setopt(CurlOpt.PROXY_CAINFO, certifi.where())

            if not self.verify:
                session.curl.setopt(CurlOpt.PROXY_SSL_VERIFYPEER, 0)
                session.curl.setopt(CurlOpt.PROXY_SSL_VERIFYHOST, 0)

        headers = self._get_impersonate_headers(request)

        if self._client_cert:
            session.curl.setopt(CurlOpt.SSLCERT, self._client_cert['client_certificate'])
            client_certificate_key = self._client_cert.get('client_certificate_key')
            client_certificate_password = self._client_cert.get('client_certificate_password')
            if client_certificate_key:
                session.curl.setopt(CurlOpt.SSLKEY, client_certificate_key)
            if client_certificate_password:
                session.curl.setopt(CurlOpt.KEYPASSWD, client_certificate_password)

        timeout = self._calculate_timeout(request)

        # set CURLOPT_LOW_SPEED_LIMIT and CURLOPT_LOW_SPEED_TIME to act as a read timeout. [1]
        # This is required only for 0.5.10 [2]
        # Note: CURLOPT_LOW_SPEED_TIME is in seconds, so we need to round up to the nearest second. [3]
        # [1] https://unix.stackexchange.com/a/305311
        # [2] https://github.com/yifeikong/curl_cffi/issues/156
        # [3] https://curl.se/libcurl/c/CURLOPT_LOW_SPEED_TIME.html
        session.curl.setopt(CurlOpt.LOW_SPEED_LIMIT, 1)  # 1 byte per second
        session.curl.setopt(CurlOpt.LOW_SPEED_TIME, math.ceil(timeout))

        try:
            curl_response = session.request(
                method=request.method,
                url=request.url,
                headers=headers,
                data=request.data,
                verify=self.verify,
                max_redirects=5,
                timeout=(timeout, timeout),
                impersonate=self._SUPPORTED_IMPERSONATE_TARGET_MAP.get(
                    self._get_request_target(request)),
                interface=self.source_address,
                stream=True,
            )
        except curl_cffi.requests.errors.RequestsError as e:
            if e.code == CurlECode.PEER_FAILED_VERIFICATION:
                raise CertificateVerifyError(cause=e) from e

            elif e.code == CurlECode.SSL_CONNECT_ERROR:
                raise SSLError(cause=e) from e

            elif e.code == CurlECode.TOO_MANY_REDIRECTS:
                max_redirects_exceeded = True
                curl_response = e.response

            elif (
                e.code == CurlECode.PROXY
                or (e.code == CurlECode.RECV_ERROR and 'CONNECT' in str(e))
            ):
                raise ProxyError(cause=e) from e
            else:
                raise TransportError(cause=e) from e

        response = CurlCFFIResponseAdapter(curl_response)

        if not 200 <= response.status < 300:
            raise HTTPError(response, redirect_loop=max_redirects_exceeded)

        return response