def _send(self, request):
        headers = self._get_headers(request)
        urllib_req = urllib.request.Request(
            url=request.url,
            data=request.data,
            headers=headers,
            method=request.method,
        )

        opener = self._get_instance(
            proxies=self._get_proxies(request),
            cookiejar=self._get_cookiejar(request),
            legacy_ssl_support=request.extensions.get('legacy_ssl'),
        )
        try:
            res = opener.open(urllib_req, timeout=self._calculate_timeout(request))
        except urllib.error.HTTPError as e:
            if isinstance(e.fp, (http.client.HTTPResponse, urllib.response.addinfourl)):
                # Prevent file object from being closed when urllib.error.HTTPError is destroyed.
                e._closer.close_called = True
                raise HTTPError(UrllibResponseAdapter(e.fp), redirect_loop='redirect error' in str(e)) from e
            raise  # unexpected
        except urllib.error.URLError as e:
            cause = e.reason  # NOTE: cause may be a string

            # proxy errors
            if 'tunnel connection failed' in str(cause).lower() or isinstance(cause, SocksProxyError):
                raise ProxyError(cause=e) from e

            handle_response_read_exceptions(cause)
            raise TransportError(cause=e) from e
        except (http.client.InvalidURL, ValueError) as e:
            # Validation errors
            # http.client.HTTPConnection raises ValueError in some validation cases
            # such as if request method contains illegal control characters [1]
            # 1. https://github.com/python/cpython/blob/987b712b4aeeece336eed24fcc87a950a756c3e2/Lib/http/client.py#L1256
            raise RequestError(cause=e) from e
        except Exception as e:
            handle_response_read_exceptions(e)
            raise  # unexpected

        return UrllibResponseAdapter(res)