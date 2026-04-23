async def wait_for_local_api_ready(
    client: httpx.AsyncClient,
    local_server: LocalAPIServer,
    timeout_seconds: float = LOCAL_API_STARTUP_TIMEOUT_SECONDS,
) -> ServerHealth:
    assert local_server.base_url is not None
    deadline = asyncio.get_running_loop().time() + timeout_seconds
    last_error: str | None = None

    while asyncio.get_running_loop().time() < deadline:
        process = local_server.process
        if process is not None and _managed_process_exit_code(process) is not None:
            if local_server._launch_mode == LOCAL_API_LAUNCH_MODE_SPAWN:
                local_server.stop()
            raise click.ClickException(
                "Local mineru-api exited before becoming healthy."
            )
        try:
            return await fetch_server_health(client, local_server.base_url)
        except click.ClickException as exc:
            last_error = str(exc)
        except httpx.HTTPError as exc:
            last_error = str(exc)
        await asyncio.sleep(TASK_STATUS_POLL_INTERVAL_SECONDS)

    message = "Timed out waiting for local mineru-api to become healthy."
    if last_error:
        message = f"{message} {last_error}"
    raise click.ClickException(message)