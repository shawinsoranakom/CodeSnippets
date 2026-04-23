def _handle_call_method_response(
            self, *, response: httpx.Response, method_name: str
        ) -> Any:
            try:
                response.raise_for_status()
                # Reset failure count on successful response
                self._connection_failure_count = 0
                return response.json()
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code

                # Try to parse the error response as RemoteCallError for mapped exceptions
                error_response = None
                try:
                    error_response = RemoteCallError.model_validate(e.response.json())
                except Exception:
                    pass

                # If we successfully parsed a mapped exception type, re-raise it
                if error_response and error_response.type in EXCEPTION_MAPPING:
                    exception_class = EXCEPTION_MAPPING[error_response.type]
                    args = error_response.args or [str(e)]

                    # Prisma DataError subclasses expect a dict `data` arg,
                    # but RPC serialization only preserves the string message
                    # from exc.args.  Wrap it in the expected structure so
                    # the constructor doesn't crash on `.get()`.
                    if issubclass(exception_class, DataError):
                        msg = str(args[0]) if args else str(e)
                        raise exception_class({"user_facing_error": {"message": msg}})

                    # GraphValidationError carries a structured ``node_errors``
                    # attribute that ``exc.args`` alone doesn't preserve.
                    # If the server included it in ``extras``, thread it
                    # back into the reconstructed exception.
                    #
                    # Identity check (``is``) is deliberate here — unlike the
                    # DataError path above which uses ``issubclass`` to catch
                    # all subclasses, GraphValidationError subclasses should
                    # fall through to the generic ``raise exception_class(*args)``
                    # below rather than silently losing their custom attributes.
                    if exception_class is exceptions.GraphValidationError:
                        msg = str(args[0]) if args else str(e)
                        node_errors = (
                            error_response.extras.node_errors
                            if error_response.extras
                            else None
                        )
                        raise exception_class(msg, node_errors=node_errors)

                    raise exception_class(*args)

                # Otherwise categorize by HTTP status code
                if 400 <= status_code < 500:
                    # Client errors (4xx) - wrap to prevent retries
                    raise HTTPClientError(status_code, str(e))
                elif 500 <= status_code < 600:
                    # Server errors (5xx) - wrap but allow retries
                    raise HTTPServerError(status_code, str(e))
                else:
                    # Other status codes (1xx, 2xx, 3xx) - re-raise original error
                    raise e