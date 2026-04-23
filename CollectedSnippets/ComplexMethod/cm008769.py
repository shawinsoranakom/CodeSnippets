def _send(self, request):
        timeout = self._calculate_timeout(request)
        headers = self._get_headers(request)
        wsuri = parse_uri(request.url)
        create_conn_kwargs = {
            'source_address': (self.source_address, 0) if self.source_address else None,
            'timeout': timeout,
        }
        proxy = select_proxy(request.url, self._get_proxies(request))
        try:
            if proxy:
                socks_proxy_options = make_socks_proxy_opts(proxy)
                sock = create_connection(
                    address=(socks_proxy_options['addr'], socks_proxy_options['port']),
                    _create_socket_func=functools.partial(
                        create_socks_proxy_socket, (wsuri.host, wsuri.port), socks_proxy_options),
                    **create_conn_kwargs,
                )
            else:
                sock = create_connection(
                    address=(wsuri.host, wsuri.port),
                    **create_conn_kwargs,
                )
            ssl_ctx = self._make_sslcontext(legacy_ssl_support=request.extensions.get('legacy_ssl'))
            conn = websockets.sync.client.connect(
                sock=sock,
                uri=request.url,
                additional_headers=headers,
                open_timeout=timeout,
                user_agent_header=None,
                ssl=ssl_ctx if wsuri.secure else None,
                close_timeout=0,  # not ideal, but prevents yt-dlp hanging
            )
            return WebsocketsResponseAdapter(conn, url=request.url)

        # Exceptions as per https://websockets.readthedocs.io/en/stable/reference/sync/client.html
        except SocksProxyError as e:
            raise ProxyError(cause=e) from e
        except websockets.exceptions.InvalidURI as e:
            raise RequestError(cause=e) from e
        except ssl.SSLCertVerificationError as e:
            raise CertificateVerifyError(cause=e) from e
        except ssl.SSLError as e:
            raise SSLError(cause=e) from e
        except websockets.exceptions.InvalidStatus as e:
            raise HTTPError(
                Response(
                    fp=io.BytesIO(e.response.body),
                    url=request.url,
                    headers=e.response.headers,
                    status=e.response.status_code,
                    reason=e.response.reason_phrase),
            ) from e
        except (OSError, TimeoutError, websockets.exceptions.WebSocketException) as e:
            raise TransportError(cause=e) from e