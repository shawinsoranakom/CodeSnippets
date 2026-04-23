def __call__(self, environ, start_response):
        """
        WSGI application entry point.

        :param dict environ: container for CGI environment variables
            such as the request HTTP headers, the source IP address and
            the body as an io file.
        :param callable start_response: function provided by the WSGI
            server that this application must call in order to send the
            HTTP response status line and the response headers.
        """
        current_thread = threading.current_thread()
        current_thread.query_count = 0
        current_thread.query_time = 0
        current_thread.perf_t0 = real_time()
        current_thread.cursor_mode = None
        if hasattr(current_thread, 'dbname'):
            del current_thread.dbname
        if hasattr(current_thread, 'uid'):
            del current_thread.uid
        thread_local.rpc_model_method = ''

        if odoo.tools.config['proxy_mode'] and environ.get("HTTP_X_FORWARDED_HOST"):
            # The ProxyFix middleware has a side effect of updating the
            # environ, see https://github.com/pallets/werkzeug/pull/2184
            def fake_app(environ, start_response):
                return []
            def fake_start_response(status, headers):
                return
            ProxyFix(fake_app)(environ, fake_start_response)

        with HTTPRequest(environ) as httprequest:
            request = Request(httprequest)
            _request_stack.push(request)

            try:
                request._post_init()
                current_thread.url = httprequest.url

                if self.get_static_file(httprequest.path):
                    response = request._serve_static()
                elif request.db:
                    try:
                        with request._get_profiler_context_manager():
                            response = request._serve_db()
                    except RegistryError as e:
                        _logger.warning("Database or registry unusable, trying without", exc_info=e.__cause__)
                        request.db = None
                        request.session.logout()
                        if (httprequest.path.startswith('/odoo/')
                            or httprequest.path in (
                                '/odoo', '/web', '/web/login', '/test_http/ensure_db',
                            )):
                            # ensure_db() protected routes, remove ?db= from the query string
                            args_nodb = request.httprequest.args.copy()
                            args_nodb.pop('db', None)
                            request.reroute(httprequest.path, url_encode(args_nodb))
                        response = request._serve_nodb()
                else:
                    response = request._serve_nodb()
                return response(environ, start_response)

            except Exception as exc:
                # Logs the error here so the traceback starts with ``__call__``.
                if hasattr(exc, 'loglevel'):
                    _logger.log(exc.loglevel, exc, exc_info=getattr(exc, 'exc_info', None))
                elif isinstance(exc, HTTPException):
                    pass
                elif isinstance(exc, SessionExpiredException):
                    _logger.info(exc)
                elif isinstance(exc, AccessError):
                    _logger.warning(exc, exc_info='access' in config['dev_mode'])
                elif isinstance(exc, UserError):
                    _logger.warning(exc)
                else:
                    _logger.exception("Exception during request handling.")

                # Ensure there is always a WSGI handler attached to the exception.
                if not hasattr(exc, 'error_response'):
                    if isinstance(exc, AccessDenied):
                        exc.suppress_traceback()
                    exc.error_response = request.dispatcher.handle_error(exc)

                return exc.error_response(environ, start_response)

            finally:
                _request_stack.pop()