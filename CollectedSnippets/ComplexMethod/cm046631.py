def _stream_with_retry(
        client: "httpx.Client",
        url: str,
        payload: dict,
        cancel_event: Optional[threading.Event] = None,
        headers: Optional[dict] = None,
    ):
        """Open an httpx streaming POST with cancel support.

        Sends the request once with a long read timeout (120 s) so
        prompt processing (prefill) can finish without triggering a
        retry storm.  The previous 0.5 s timeout caused duplicate POST
        requests every half second, forcing llama-server to restart
        processing each time.

        A background watcher thread provides cancel by closing the
        response when cancel_event is set.  Limitation: httpx does not
        allow interrupting a blocked read from another thread before
        the response object exists, so cancel during the initial
        header wait (prefill phase) only takes effect once headers
        arrive.  After that, response.close() unblocks reads promptly.
        In practice llama-server prefill is 1-5 s for typical prompts,
        during which cancel is deferred -- still much better than the
        old retry storm which made prefill slower.
        """
        if cancel_event is not None and cancel_event.is_set():
            raise GeneratorExit

        # Background watcher: close the response if cancel is requested.
        # Only effective after response headers arrive (httpx limitation).
        _cancel_closed = threading.Event()
        _response_ref: list = [None]

        def _cancel_watcher():
            while not _cancel_closed.is_set():
                if cancel_event.wait(timeout = 0.3):
                    # Cancel requested. Keep polling until the response object
                    # exists so we can close it, or until the main thread
                    # finishes on its own (_cancel_closed is set in finally).
                    while not _cancel_closed.is_set():
                        r = _response_ref[0]
                        if r is not None:
                            try:
                                r.close()
                                return
                            except Exception as e:
                                logger.debug(
                                    f"Error closing response in cancel watcher: {e}"
                                )
                        # Response not created yet -- wait briefly and retry
                        _cancel_closed.wait(timeout = 0.1)
                    return

        watcher = None
        if cancel_event is not None:
            watcher = threading.Thread(
                target = _cancel_watcher, daemon = True, name = "prefill-cancel"
            )
            watcher.start()

        try:
            # Long read timeout so prefill (prompt processing) can finish
            # without triggering a retry storm.  Cancel during both
            # prefill and streaming is handled by the watcher thread
            # which closes the response, unblocking any httpx read.
            prefill_timeout = httpx.Timeout(
                connect = 30,
                read = 120.0,
                write = 10,
                pool = 10,
            )
            with client.stream(
                "POST",
                url,
                json = payload,
                timeout = prefill_timeout,
                headers = headers,
            ) as response:
                _response_ref[0] = response
                if cancel_event is not None and cancel_event.is_set():
                    raise GeneratorExit
                yield response
                return
        except (httpx.ReadError, httpx.RemoteProtocolError, httpx.CloseError):
            # Response was closed by the cancel watcher
            if cancel_event is not None and cancel_event.is_set():
                raise GeneratorExit
            raise
        finally:
            _cancel_closed.set()