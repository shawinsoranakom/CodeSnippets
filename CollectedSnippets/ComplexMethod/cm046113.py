async def run_demo(
    input_path: str | Path,
    output_dir: str | Path,
    *,
    api_url: str | None = None,
    backend: str = "hybrid-auto-engine",
    parse_method: str = "auto",
    language: str = "ch",
    formula_enable: bool = True,
    table_enable: bool = True,
    server_url: str | None = None,
    start_page_id: int = 0,
    end_page_id: int | None = None,
) -> None:
    api_url = api_url or None
    server_url = server_url or None
    if backend.endswith("http-client") and not server_url:
        raise ValueError(f"backend={backend} requires server_url")

    input_files = collect_input_files(input_path)
    output_path = Path(output_dir).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    form_data = build_form_data(
        language=language,
        backend=backend,
        parse_method=parse_method,
        formula_enable=formula_enable,
        table_enable=table_enable,
        server_url=server_url,
        start_page_id=start_page_id,
        end_page_id=end_page_id,
    )
    upload_assets = [
        _api_client.UploadAsset(path=file_path, upload_name=file_path.name)
        for file_path in input_files
    ]

    local_server: _api_client.LocalAPIServer | None = None
    result_zip_path: Path | None = None
    task_label = f"{len(input_files)} file(s)"

    async with httpx.AsyncClient(
        timeout=_api_client.build_http_timeout(),
        follow_redirects=True,
    ) as http_client:
        try:
            if api_url is None:
                prepare_local_api_temp_dir()
                local_server = _api_client.LocalAPIServer()
                base_url = local_server.start()
                print(f"Started local mineru-api: {base_url}")
                server_health = await _api_client.wait_for_local_api_ready(
                    http_client,
                    local_server,
                )
            else:
                server_health = await _api_client.fetch_server_health(
                    http_client,
                    _api_client.normalize_base_url(api_url),
                )

            print(f"Using API: {server_health.base_url}")
            print(f"Submitting {len(upload_assets)} file(s)")
            submit_response = await _api_client.submit_parse_task(
                base_url=server_health.base_url,
                upload_assets=upload_assets,
                form_data=form_data,
            )
            print(f"task_id: {submit_response.task_id}")
            if submit_response.queued_ahead is not None:
                print(f"status: pending (queued_ahead={submit_response.queued_ahead})")

            last_status_message = None

            def on_status_update(status_snapshot: _api_client.TaskStatusSnapshot) -> None:
                nonlocal last_status_message
                message = format_status_message(status_snapshot)
                if message == last_status_message:
                    return
                last_status_message = message
                print(f"status: {message}")

            await _api_client.wait_for_task_result(
                client=http_client,
                submit_response=submit_response,
                task_label=task_label,
                status_snapshot_callback=on_status_update,
            )
            print("status: completed")
            result_zip_path = await _api_client.download_result_zip(
                client=http_client,
                submit_response=submit_response,
                task_label=task_label,
            )
        finally:
            if local_server is not None:
                local_server.stop()

    assert result_zip_path is not None
    try:
        _api_client.safe_extract_zip(result_zip_path, output_path)
    finally:
        result_zip_path.unlink(missing_ok=True)
    print(f"Extracted result to: {output_path}")