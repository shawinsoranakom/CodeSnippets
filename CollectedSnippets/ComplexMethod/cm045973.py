async def wait_for_task_result(
    client: httpx.AsyncClient,
    submit_response: SubmitResponse,
    task_label: str,
    *,
    status_callback: Optional[Callable[[str], None]] = None,
    status_snapshot_callback: Optional[Callable[[TaskStatusSnapshot], None]] = None,
    timeout_seconds: float = TASK_RESULT_TIMEOUT_SECONDS,
) -> None:
    deadline = asyncio.get_running_loop().time() + timeout_seconds
    while asyncio.get_running_loop().time() < deadline:
        try:
            response = await client.get(submit_response.status_url)
        except httpx.ReadTimeout:
            logger.warning(
                "Timed out while polling task status for {} (task_id={}). "
                "This can happen during cold start; retrying until the task deadline.",
                task_label,
                submit_response.task_id,
            )
            await asyncio.sleep(TASK_STATUS_POLL_INTERVAL_SECONDS)
            continue
        if response.status_code != 200:
            raise click.ClickException(
                f"Failed to query task status for {task_label}: "
                f"{response.status_code} {response_detail(response)}"
            )

        payload = response.json()
        status = payload.get("status")
        if status in {"pending", "processing"}:
            queued_ahead = payload.get("queued_ahead")
            if not isinstance(queued_ahead, int):
                queued_ahead = None
            if status_snapshot_callback is not None:
                status_snapshot_callback(
                    TaskStatusSnapshot(
                        status=status,
                        queued_ahead=queued_ahead,
                    )
                )
            if status_callback is not None:
                status_callback(status)
            await asyncio.sleep(TASK_STATUS_POLL_INTERVAL_SECONDS)
            continue
        if status == "completed":
            return
        raise click.ClickException(
            f"Task {submit_response.task_id} failed for {task_label}: "
            f"{json.dumps(payload, ensure_ascii=False)}"
        )

    raise click.ClickException(
        f"Timed out waiting for result of task {submit_response.task_id} "
        f"for {task_label}"
    )