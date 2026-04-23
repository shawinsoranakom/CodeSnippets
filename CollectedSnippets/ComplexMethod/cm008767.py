def _check_proxies(self, proxies):
        for proxy_key, proxy_url in proxies.items():
            if proxy_url is None:
                continue
            if proxy_key == 'no':
                if self._SUPPORTED_FEATURES is not None and Features.NO_PROXY not in self._SUPPORTED_FEATURES:
                    raise UnsupportedRequest('"no" proxy is not supported')
                continue
            if (
                proxy_key == 'all'
                and self._SUPPORTED_FEATURES is not None
                and Features.ALL_PROXY not in self._SUPPORTED_FEATURES
            ):
                raise UnsupportedRequest('"all" proxy is not supported')

            # Unlikely this handler will use this proxy, so ignore.
            # This is to allow a case where a proxy may be set for a protocol
            # for one handler in which such protocol (and proxy) is not supported by another handler.
            if self._SUPPORTED_URL_SCHEMES is not None and proxy_key not in (*self._SUPPORTED_URL_SCHEMES, 'all'):
                continue

            if self._SUPPORTED_PROXY_SCHEMES is None:
                # Skip proxy scheme checks
                continue

            try:
                if urllib.request._parse_proxy(proxy_url)[0] is None:
                    # Scheme-less proxies are not supported
                    raise UnsupportedRequest(f'Proxy "{proxy_url}" missing scheme')
            except ValueError as e:
                # parse_proxy may raise on some invalid proxy urls such as "/a/b/c"
                raise UnsupportedRequest(f'Invalid proxy url "{proxy_url}": {e}')

            scheme = urllib.parse.urlparse(proxy_url).scheme.lower()
            if scheme not in self._SUPPORTED_PROXY_SCHEMES:
                raise UnsupportedRequest(f'Unsupported proxy type: "{scheme}"')