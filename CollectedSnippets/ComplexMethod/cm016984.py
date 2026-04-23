async def _request_base(cfg: _RequestConfig, expect_binary: bool):
    """Core request with retries, per-second interruption monitoring, true cancellation, and friendly errors."""
    url = cfg.endpoint.path
    parsed_url = urlparse(url)
    if not parsed_url.scheme and not parsed_url.netloc:  # is URL relative?
        url = urljoin(default_base_url().rstrip("/") + "/", url.lstrip("/"))

    method = cfg.endpoint.method
    params = _merge_params(cfg.endpoint.query_params, method, cfg.data if method == "GET" else None)

    async def _monitor(stop_evt: asyncio.Event, start_ts: float):
        """Every second: update elapsed time and signal interruption."""
        try:
            while not stop_evt.is_set():
                if is_processing_interrupted():
                    return
                if cfg.monitor_progress:
                    _display_time_progress(
                        cfg.node_cls, cfg.wait_label, int(time.monotonic() - start_ts), cfg.estimated_total
                    )
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            return  # normal shutdown

    start_time = cfg.progress_origin_ts if cfg.progress_origin_ts is not None else time.monotonic()
    attempt = 0
    delay = cfg.retry_delay
    rate_limit_attempts = 0
    rate_limit_delay = cfg.retry_delay
    operation_succeeded: bool = False
    final_elapsed_seconds: int | None = None
    extracted_price: float | None = None
    while True:
        attempt += 1
        stop_event = asyncio.Event()
        monitor_task: asyncio.Task | None = None
        sess: aiohttp.ClientSession | None = None

        operation_id = _generate_operation_id(method, cfg.endpoint.path, attempt)
        logging.debug("[DEBUG] HTTP %s %s (attempt %d)", method, url, attempt)

        payload_headers = {"Accept": "*/*"} if expect_binary else {"Accept": "application/json"}
        if not parsed_url.scheme and not parsed_url.netloc:  # is URL relative?
            payload_headers.update(get_auth_header(cfg.node_cls))
        if cfg.endpoint.headers:
            payload_headers.update(cfg.endpoint.headers)

        payload_kw: dict[str, Any] = {"headers": payload_headers}
        if method == "GET":
            payload_headers.pop("Content-Type", None)
        request_body_log = _snapshot_request_body_for_logging(cfg.content_type, method, cfg.data, cfg.files)
        try:
            if cfg.monitor_progress:
                monitor_task = asyncio.create_task(_monitor(stop_event, start_time))

            timeout = aiohttp.ClientTimeout(total=cfg.timeout)
            sess = aiohttp.ClientSession(timeout=timeout)

            if cfg.content_type == "multipart/form-data" and method != "GET":
                # aiohttp will set Content-Type boundary; remove any fixed Content-Type
                payload_headers.pop("Content-Type", None)
                if cfg.multipart_parser and cfg.data:
                    form = cfg.multipart_parser(cfg.data)
                    if not isinstance(form, aiohttp.FormData):
                        raise ValueError("multipart_parser must return aiohttp.FormData")
                else:
                    form = aiohttp.FormData(default_to_multipart=True)
                    if cfg.data:
                        for k, v in cfg.data.items():
                            if v is None:
                                continue
                            form.add_field(k, str(v) if not isinstance(v, (bytes, bytearray)) else v)
                if cfg.files:
                    file_iter = cfg.files if isinstance(cfg.files, list) else cfg.files.items()
                    for field_name, file_obj in file_iter:
                        if file_obj is None:
                            continue
                        if isinstance(file_obj, tuple):
                            filename, file_value, content_type = _unpack_tuple(file_obj)
                        else:
                            filename = getattr(file_obj, "name", field_name)
                            file_value = file_obj
                            content_type = "application/octet-stream"
                        # Attempt to rewind BytesIO for retries
                        if isinstance(file_value, BytesIO):
                            with contextlib.suppress(Exception):
                                file_value.seek(0)
                        form.add_field(field_name, file_value, filename=filename, content_type=content_type)
                payload_kw["data"] = form
            elif cfg.content_type == "application/x-www-form-urlencoded" and method != "GET":
                payload_headers["Content-Type"] = "application/x-www-form-urlencoded"
                payload_kw["data"] = cfg.data or {}
            elif method != "GET":
                payload_headers["Content-Type"] = "application/json"
                payload_kw["json"] = cfg.data or {}

            request_logger.log_request_response(
                operation_id=operation_id,
                request_method=method,
                request_url=url,
                request_headers=dict(payload_headers) if payload_headers else None,
                request_params=dict(params) if params else None,
                request_data=request_body_log,
            )

            req_coro = sess.request(method, url, params=params, **payload_kw)
            req_task = asyncio.create_task(req_coro)

            # Race: request vs. monitor (interruption)
            tasks = {req_task}
            if monitor_task:
                tasks.add(monitor_task)
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            if monitor_task and monitor_task in done:
                # Interrupted – cancel the request and abort
                if req_task in pending:
                    req_task.cancel()
                raise ProcessingInterrupted("Task cancelled")

            # Otherwise, request finished
            resp = await req_task
            async with resp:
                if resp.status >= 400:
                    try:
                        body = await resp.json()
                    except (ContentTypeError, json.JSONDecodeError):
                        body = await resp.text()
                    should_retry = False
                    wait_time = 0.0
                    retry_label = ""
                    is_rl = resp.status == 429 or (
                        cfg.is_rate_limited is not None and cfg.is_rate_limited(resp.status, body)
                    )
                    if is_rl and rate_limit_attempts < cfg.max_retries_on_rate_limit:
                        rate_limit_attempts += 1
                        wait_time = min(rate_limit_delay, 30.0)
                        rate_limit_delay *= cfg.retry_backoff
                        retry_label = f"rate-limit retry {rate_limit_attempts} of {cfg.max_retries_on_rate_limit}"
                        should_retry = True
                    elif resp.status in _RETRY_STATUS and (attempt - rate_limit_attempts) <= cfg.max_retries:
                        wait_time = delay
                        delay *= cfg.retry_backoff
                        retry_label = f"retry {attempt - rate_limit_attempts} of {cfg.max_retries}"
                        should_retry = True

                    if should_retry:
                        logging.warning(
                            "HTTP %s %s -> %s. Waiting %.2fs (%s).",
                            method,
                            url,
                            resp.status,
                            wait_time,
                            retry_label,
                        )
                        request_logger.log_request_response(
                            operation_id=operation_id,
                            request_method=method,
                            request_url=url,
                            response_status_code=resp.status,
                            response_headers=dict(resp.headers),
                            response_content=body,
                            error_message=f"HTTP {resp.status} ({retry_label}, will retry in {wait_time:.1f}s)",
                        )
                        await sleep_with_interrupt(
                            wait_time,
                            cfg.node_cls,
                            cfg.wait_label if cfg.monitor_progress else None,
                            start_time if cfg.monitor_progress else None,
                            cfg.estimated_total,
                            display_callback=_display_time_progress if cfg.monitor_progress else None,
                        )
                        continue
                    msg = _friendly_http_message(resp.status, body)
                    request_logger.log_request_response(
                        operation_id=operation_id,
                        request_method=method,
                        request_url=url,
                        response_status_code=resp.status,
                        response_headers=dict(resp.headers),
                        response_content=body,
                        error_message=msg,
                    )
                    raise Exception(msg)

                if expect_binary:
                    buff = bytearray()
                    last_tick = time.monotonic()
                    async for chunk in resp.content.iter_chunked(64 * 1024):
                        buff.extend(chunk)
                        now = time.monotonic()
                        if now - last_tick >= 1.0:
                            last_tick = now
                            if is_processing_interrupted():
                                raise ProcessingInterrupted("Task cancelled")
                            if cfg.monitor_progress:
                                _display_time_progress(
                                    cfg.node_cls, cfg.wait_label, int(now - start_time), cfg.estimated_total
                                )
                    bytes_payload = bytes(buff)
                    resp_headers = {k.lower(): v for k, v in resp.headers.items()}
                    if cfg.price_extractor:
                        with contextlib.suppress(Exception):
                            extracted_price = cfg.price_extractor(resp_headers)
                    if cfg.response_header_validator:
                        cfg.response_header_validator(resp_headers)
                    operation_succeeded = True
                    final_elapsed_seconds = int(time.monotonic() - start_time)
                    request_logger.log_request_response(
                        operation_id=operation_id,
                        request_method=method,
                        request_url=url,
                        response_status_code=resp.status,
                        response_headers=resp_headers,
                        response_content=bytes_payload,
                    )
                    return bytes_payload
                else:
                    try:
                        payload = await resp.json()
                        response_content_to_log: Any = payload
                    except (ContentTypeError, json.JSONDecodeError):
                        text = await resp.text()
                        try:
                            payload = json.loads(text) if text else {}
                        except json.JSONDecodeError:
                            payload = {"_raw": text}
                        response_content_to_log = payload if isinstance(payload, dict) else text
                    with contextlib.suppress(Exception):
                        extracted_price = cfg.price_extractor(payload) if cfg.price_extractor else None
                    operation_succeeded = True
                    final_elapsed_seconds = int(time.monotonic() - start_time)
                    request_logger.log_request_response(
                        operation_id=operation_id,
                        request_method=method,
                        request_url=url,
                        response_status_code=resp.status,
                        response_headers=dict(resp.headers),
                        response_content=response_content_to_log,
                    )
                    return payload

        except ProcessingInterrupted:
            logging.debug("Polling was interrupted by user")
            raise
        except (ClientError, OSError) as e:
            if (attempt - rate_limit_attempts) <= cfg.max_retries:
                logging.warning(
                    "Connection error calling %s %s. Retrying in %.2fs (%d/%d): %s",
                    method,
                    url,
                    delay,
                    attempt - rate_limit_attempts,
                    cfg.max_retries,
                    str(e),
                )
                request_logger.log_request_response(
                    operation_id=operation_id,
                    request_method=method,
                    request_url=url,
                    request_headers=dict(payload_headers) if payload_headers else None,
                    request_params=dict(params) if params else None,
                    request_data=request_body_log,
                    error_message=f"{type(e).__name__}: {str(e)} (will retry)",
                )
                await sleep_with_interrupt(
                    delay,
                    cfg.node_cls,
                    cfg.wait_label if cfg.monitor_progress else None,
                    start_time if cfg.monitor_progress else None,
                    cfg.estimated_total,
                    display_callback=_display_time_progress if cfg.monitor_progress else None,
                )
                delay *= cfg.retry_backoff
                continue
            diag = await _diagnose_connectivity()
            if not diag["internet_accessible"]:
                request_logger.log_request_response(
                    operation_id=operation_id,
                    request_method=method,
                    request_url=url,
                    request_headers=dict(payload_headers) if payload_headers else None,
                    request_params=dict(params) if params else None,
                    request_data=request_body_log,
                    error_message=f"LocalNetworkError: {str(e)}",
                )
                raise LocalNetworkError(
                    "Unable to connect to the API server due to local network issues. "
                    "Please check your internet connection and try again."
                ) from e
            request_logger.log_request_response(
                operation_id=operation_id,
                request_method=method,
                request_url=url,
                request_headers=dict(payload_headers) if payload_headers else None,
                request_params=dict(params) if params else None,
                request_data=request_body_log,
                error_message=f"ApiServerError: {str(e)}",
            )
            raise ApiServerError(
                f"The API server at {default_base_url()} is currently unreachable. "
                f"The service may be experiencing issues."
            ) from e
        finally:
            stop_event.set()
            if monitor_task:
                monitor_task.cancel()
                with contextlib.suppress(Exception):
                    await monitor_task
            if sess:
                with contextlib.suppress(Exception):
                    await sess.close()
            if operation_succeeded and cfg.monitor_progress and cfg.final_label_on_success:
                _display_time_progress(
                    cfg.node_cls,
                    status=cfg.final_label_on_success,
                    elapsed_seconds=(
                        final_elapsed_seconds
                        if final_elapsed_seconds is not None
                        else int(time.monotonic() - start_time)
                    ),
                    estimated_total=cfg.estimated_total,
                    price=extracted_price,
                    is_queued=False,
                    processing_elapsed_seconds=final_elapsed_seconds,
                )