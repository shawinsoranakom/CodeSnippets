def urlopen(self, req):
        """ Start an HTTP download """
        if isinstance(req, str):
            req = Request(req)
        elif isinstance(req, urllib.request.Request):
            self.deprecation_warning(
                'Passing a urllib.request.Request object to YoutubeDL.urlopen() is deprecated. '
                'Use yt_dlp.networking.common.Request instead.')
            req = urllib_req_to_req(req)
        assert isinstance(req, Request)

        # compat: Assume user:pass url params are basic auth
        url, basic_auth_header = extract_basic_auth(req.url)
        if basic_auth_header:
            req.headers['Authorization'] = basic_auth_header
        req.url = sanitize_url(url)

        clean_proxies(proxies=req.proxies, headers=req.headers)
        clean_headers(req.headers)

        try:
            return self._request_director.send(req)
        except NoSupportingHandlers as e:
            for ue in e.unsupported_errors:
                # FIXME: This depends on the order of errors.
                if not (ue.handler and ue.msg):
                    continue
                if ue.handler.RH_KEY == 'Urllib' and 'unsupported url scheme: "file"' in ue.msg.lower():
                    raise RequestError(
                        'file:// URLs are disabled by default in yt-dlp for security reasons. '
                        'Use --enable-file-urls to enable at your own risk.', cause=ue) from ue
                if (
                    'unsupported proxy type: "https"' in ue.msg.lower()
                    and 'requests' not in self._request_director.handlers
                    and 'curl_cffi' not in self._request_director.handlers
                ):
                    raise RequestError(
                        'To use an HTTPS proxy for this request, one of the following dependencies needs to be installed: requests, curl_cffi')

                elif (
                    re.match(r'unsupported url scheme: "wss?"', ue.msg.lower())
                    and 'websockets' not in self._request_director.handlers
                ):
                    raise RequestError(
                        'This request requires WebSocket support. '
                        'Ensure one of the following dependencies are installed: websockets',
                        cause=ue) from ue

                elif re.match(r'unsupported (?:extensions: impersonate|impersonate target)', ue.msg.lower()):
                    raise RequestError(
                        f'Impersonate target "{req.extensions["impersonate"]}" is not available.'
                        f' See --list-impersonate-targets for available targets.'
                        f' This request requires browser impersonation, however you may be missing dependencies'
                        f' required to support this target.')
            raise
        except SSLError as e:
            if 'UNSAFE_LEGACY_RENEGOTIATION_DISABLED' in str(e):
                raise RequestError('UNSAFE_LEGACY_RENEGOTIATION_DISABLED: Try using --legacy-server-connect', cause=e) from e
            elif 'SSLV3_ALERT_HANDSHAKE_FAILURE' in str(e):
                raise RequestError(
                    'SSLV3_ALERT_HANDSHAKE_FAILURE: The server may not support the current cipher list. '
                    'Try using --legacy-server-connect', cause=e) from e
            raise