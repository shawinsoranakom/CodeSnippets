async def upload_file(
    cls: type[IO.ComfyNode],
    upload_url: str,
    file: BytesIO | str,
    *,
    content_type: str | None = None,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    retry_backoff: float = 2.0,
    wait_label: str | None = None,
    progress_origin_ts: float | None = None,
) -> None:
    """
    Upload a file to a signed URL (e.g., S3 pre-signed PUT) with retries, Comfy progress display, and interruption.

    Raises:
        ProcessingInterrupted, LocalNetworkError, ApiServerError, Exception
    """
    if isinstance(file, BytesIO):
        with contextlib.suppress(Exception):
            file.seek(0)
        data = file.read()
    elif isinstance(file, str):
        with open(file, "rb") as f:
            data = f.read()
    else:
        raise ValueError("file must be a BytesIO or a filesystem path string")

    headers: dict[str, str] = {}
    skip_auto_headers: set[str] = set()
    if content_type:
        headers["Content-Type"] = content_type
    else:
        skip_auto_headers.add("Content-Type")  # Don't let aiohttp add Content-Type, it can break the signed request

    attempt = 0
    delay = retry_delay
    start_ts = progress_origin_ts if progress_origin_ts is not None else time.monotonic()
    op_uuid = uuid.uuid4().hex[:8]
    while True:
        attempt += 1
        operation_id = _generate_operation_id("PUT", upload_url, attempt, op_uuid)
        timeout = aiohttp.ClientTimeout(total=None)
        stop_evt = asyncio.Event()

        async def _monitor():
            try:
                while not stop_evt.is_set():
                    if is_processing_interrupted():
                        return
                    if wait_label:
                        _display_time_progress(cls, wait_label, int(time.monotonic() - start_ts), None)
                    await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                return

        monitor_task = asyncio.create_task(_monitor())
        sess: aiohttp.ClientSession | None = None
        try:
            request_logger.log_request_response(
                operation_id=operation_id,
                request_method="PUT",
                request_url=upload_url,
                request_headers=headers or None,
                request_params=None,
                request_data=f"[File data {len(data)} bytes]",
            )

            sess = aiohttp.ClientSession(timeout=timeout)
            req = sess.put(upload_url, data=data, headers=headers, skip_auto_headers=skip_auto_headers)
            req_task = asyncio.create_task(req)

            done, pending = await asyncio.wait({req_task, monitor_task}, return_when=asyncio.FIRST_COMPLETED)

            if monitor_task in done and req_task in pending:
                req_task.cancel()
                raise ProcessingInterrupted("Upload cancelled")

            try:
                resp = await req_task
            except asyncio.CancelledError:
                raise ProcessingInterrupted("Upload cancelled") from None

            async with resp:
                if resp.status >= 400:
                    with contextlib.suppress(Exception):
                        try:
                            body = await resp.json()
                        except Exception:
                            body = await resp.text()
                        msg = f"Upload failed with status {resp.status}"
                        request_logger.log_request_response(
                            operation_id=operation_id,
                            request_method="PUT",
                            request_url=upload_url,
                            response_status_code=resp.status,
                            response_headers=dict(resp.headers),
                            response_content=body,
                            error_message=msg,
                        )
                    if resp.status in {408, 429, 500, 502, 503, 504} and attempt <= max_retries:
                        await sleep_with_interrupt(
                            delay,
                            cls,
                            wait_label,
                            start_ts,
                            None,
                            display_callback=_display_time_progress if wait_label else None,
                        )
                        delay *= retry_backoff
                        continue
                    raise Exception(f"Failed to upload (HTTP {resp.status}).")
                request_logger.log_request_response(
                    operation_id=operation_id,
                    request_method="PUT",
                    request_url=upload_url,
                    response_status_code=resp.status,
                    response_headers=dict(resp.headers),
                    response_content="File uploaded successfully.",
                )
                return
        except asyncio.CancelledError:
            raise ProcessingInterrupted("Task cancelled") from None
        except (aiohttp.ClientError, OSError) as e:
            if attempt <= max_retries:
                request_logger.log_request_response(
                    operation_id=operation_id,
                    request_method="PUT",
                    request_url=upload_url,
                    request_headers=headers or None,
                    request_data=f"[File data {len(data)} bytes]",
                    error_message=f"{type(e).__name__}: {str(e)} (will retry)",
                )
                await sleep_with_interrupt(
                    delay,
                    cls,
                    wait_label,
                    start_ts,
                    None,
                    display_callback=_display_time_progress if wait_label else None,
                )
                delay *= retry_backoff
                continue

            diag = await _diagnose_connectivity()
            if not diag["internet_accessible"]:
                raise LocalNetworkError(
                    "Unable to connect to the network. Please check your internet connection and try again."
                ) from e
            raise ApiServerError("The API service appears unreachable at this time.") from e
        finally:
            stop_evt.set()
            if monitor_task:
                monitor_task.cancel()
                with contextlib.suppress(Exception):
                    await monitor_task
            if sess:
                with contextlib.suppress(Exception):
                    await sess.close()