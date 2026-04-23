async def poll_op_raw(
    cls: type[IO.ComfyNode],
    poll_endpoint: ApiEndpoint,
    *,
    status_extractor: Callable[[dict[str, Any]], str | int | None],
    progress_extractor: Callable[[dict[str, Any]], int | None] | None = None,
    price_extractor: Callable[[dict[str, Any]], float | None] | None = None,
    completed_statuses: list[str | int] | None = None,
    failed_statuses: list[str | int] | None = None,
    queued_statuses: list[str | int] | None = None,
    data: dict[str, Any] | BaseModel | None = None,
    poll_interval: float = 5.0,
    max_poll_attempts: int = 160,
    timeout_per_poll: float = 120.0,
    max_retries_per_poll: int = 10,
    retry_delay_per_poll: float = 1.0,
    retry_backoff_per_poll: float = 1.4,
    estimated_duration: int | None = None,
    cancel_endpoint: ApiEndpoint | None = None,
    cancel_timeout: float = 10.0,
    extra_text: str | None = None,
) -> dict[str, Any]:
    """
    Polls an endpoint until the task reaches a terminal state. Displays time while queued/processing,
    checks interruption every second, and calls Cancel endpoint (if provided) on interruption.

    Uses default complete, failed and queued states assumption.

    Returns the final JSON response from the poll endpoint.
    """
    completed_states = _normalize_statuses(COMPLETED_STATUSES if completed_statuses is None else completed_statuses)
    failed_states = _normalize_statuses(FAILED_STATUSES if failed_statuses is None else failed_statuses)
    queued_states = _normalize_statuses(QUEUED_STATUSES if queued_statuses is None else queued_statuses)
    started = time.monotonic()
    consumed_attempts = 0  # counts only non-queued polls

    progress_bar = utils.ProgressBar(100) if progress_extractor else None
    last_progress: int | None = None

    state = _PollUIState(started=started, estimated_duration=estimated_duration)
    stop_ticker = asyncio.Event()

    async def _ticker():
        """Emit a UI update every second while polling is in progress."""
        try:
            while not stop_ticker.is_set():
                if is_processing_interrupted():
                    break
                now = time.monotonic()
                proc_elapsed = state.base_processing_elapsed + (
                    (now - state.active_since) if state.active_since is not None else 0.0
                )
                _display_time_progress(
                    cls,
                    status=state.status_label,
                    elapsed_seconds=int(now - state.started),
                    estimated_total=state.estimated_duration,
                    price=state.price,
                    is_queued=state.is_queued,
                    processing_elapsed_seconds=int(proc_elapsed),
                    extra_text=extra_text,
                )
                await asyncio.sleep(1.0)
        except Exception as exc:
            logging.debug("Polling ticker exited: %s", exc)

    ticker_task = asyncio.create_task(_ticker())
    try:
        while consumed_attempts < max_poll_attempts:
            try:
                resp_json = await sync_op_raw(
                    cls,
                    poll_endpoint,
                    data=data,
                    timeout=timeout_per_poll,
                    max_retries=max_retries_per_poll,
                    retry_delay=retry_delay_per_poll,
                    retry_backoff=retry_backoff_per_poll,
                    wait_label="Checking",
                    estimated_duration=None,
                    as_binary=False,
                    final_label_on_success=None,
                    monitor_progress=False,
                )
                if not isinstance(resp_json, dict):
                    raise Exception("Polling endpoint returned non-JSON response.")
            except ProcessingInterrupted:
                if cancel_endpoint:
                    with contextlib.suppress(Exception):
                        await sync_op_raw(
                            cls,
                            cancel_endpoint,
                            timeout=cancel_timeout,
                            max_retries=0,
                            wait_label="Cancelling task",
                            estimated_duration=None,
                            as_binary=False,
                            final_label_on_success=None,
                            monitor_progress=False,
                        )
                raise

            try:
                status = _normalize_status_value(status_extractor(resp_json))
            except Exception as e:
                logging.error("Status extraction failed: %s", e)
                status = None

            if price_extractor:
                new_price = price_extractor(resp_json)
                if new_price is not None:
                    state.price = new_price

            if progress_extractor:
                new_progress = progress_extractor(resp_json)
                if new_progress is not None and last_progress != new_progress:
                    progress_bar.update_absolute(new_progress, total=100)
                    last_progress = new_progress

            now_ts = time.monotonic()
            is_queued = status in queued_states

            if is_queued:
                if state.active_since is not None:  # If we just moved from active -> queued, close the active interval
                    state.base_processing_elapsed += now_ts - state.active_since
                    state.active_since = None
            else:
                if state.active_since is None:  # If we just moved from queued -> active, open a new active interval
                    state.active_since = now_ts

            state.is_queued = is_queued
            state.status_label = status or ("Queued" if is_queued else "Processing")
            if status in completed_states:
                if state.active_since is not None:
                    state.base_processing_elapsed += now_ts - state.active_since
                    state.active_since = None
                stop_ticker.set()
                with contextlib.suppress(Exception):
                    await ticker_task

                if progress_bar and last_progress != 100:
                    progress_bar.update_absolute(100, total=100)

                _display_time_progress(
                    cls,
                    status=status if status else "Completed",
                    elapsed_seconds=int(now_ts - started),
                    estimated_total=estimated_duration,
                    price=state.price,
                    is_queued=False,
                    processing_elapsed_seconds=int(state.base_processing_elapsed),
                    extra_text=extra_text,
                )
                return resp_json

            if status in failed_states:
                msg = f"Task failed: {json.dumps(resp_json)}"
                logging.error(msg)
                raise Exception(msg)

            try:
                await sleep_with_interrupt(poll_interval, cls, None, None, None)
            except ProcessingInterrupted:
                if cancel_endpoint:
                    with contextlib.suppress(Exception):
                        await sync_op_raw(
                            cls,
                            cancel_endpoint,
                            timeout=cancel_timeout,
                            max_retries=0,
                            wait_label="Cancelling task",
                            estimated_duration=None,
                            as_binary=False,
                            final_label_on_success=None,
                            monitor_progress=False,
                        )
                raise
            if not is_queued:
                consumed_attempts += 1

        raise Exception(
            f"Polling timed out after {max_poll_attempts} non-queued attempts "
            f"(~{int(max_poll_attempts * poll_interval)}s of active polling)."
        )
    except ProcessingInterrupted:
        raise
    except (LocalNetworkError, ApiServerError):
        raise
    except Exception as e:
        raise Exception(f"Polling aborted due to error: {e}") from e
    finally:
        stop_ticker.set()
        with contextlib.suppress(Exception):
            await ticker_task