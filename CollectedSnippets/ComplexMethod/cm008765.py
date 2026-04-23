def _send(self, request):

        headers = self._get_headers(request)
        max_redirects_exceeded = False

        session = self._get_instance(
            cookiejar=self._get_cookiejar(request),
            legacy_ssl_support=request.extensions.get('legacy_ssl'),
        )

        try:
            requests_res = session.request(
                method=request.method,
                url=request.url,
                data=request.data,
                headers=headers,
                timeout=self._calculate_timeout(request),
                proxies=self._get_proxies(request),
                allow_redirects=True,
                stream=True,
            )

        except requests.exceptions.TooManyRedirects as e:
            max_redirects_exceeded = True
            requests_res = e.response

        except requests.exceptions.SSLError as e:
            if 'CERTIFICATE_VERIFY_FAILED' in str(e):
                raise CertificateVerifyError(cause=e) from e
            raise SSLError(cause=e) from e

        except requests.exceptions.ProxyError as e:
            raise ProxyError(cause=e) from e

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            raise TransportError(cause=e) from e

        except urllib3.exceptions.HTTPError as e:
            # Catch any urllib3 exceptions that may leak through
            raise TransportError(cause=e) from e

        except requests.exceptions.RequestException as e:
            # Miscellaneous Requests exceptions. May not necessary be network related e.g. InvalidURL
            raise RequestError(cause=e) from e

        res = RequestsResponseAdapter(requests_res)

        if not 200 <= res.status < 300:
            raise HTTPError(res, redirect_loop=max_redirects_exceeded)

        return res