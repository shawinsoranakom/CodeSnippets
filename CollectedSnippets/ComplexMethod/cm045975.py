async def run_orchestrated_cli(
    input_path: Path,
    output_dir: Path,
    method: str,
    backend: str,
    lang: str,
    server_url: Optional[str],
    api_url: Optional[str],
    start_page_id: int,
    end_page_id: Optional[int],
    formula_enable: bool,
    table_enable: bool,
    extra_cli_args: tuple[str, ...] = (),
) -> None:
    if start_page_id < 0:
        raise click.ClickException("--start must be greater than or equal to 0")
    if end_page_id is not None and end_page_id < 0:
        raise click.ClickException("--end must be greater than or equal to 0")
    if api_url is None:
        try:
            ensure_backend_dependencies(backend)
        except HybridDependencyError as exc:
            raise click.ClickException(str(exc)) from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    documents = collect_input_documents(
        input_path=input_path,
        start_page_id=start_page_id,
        end_page_id=end_page_id,
    )

    timeout = build_http_timeout()
    local_server: LocalAPIServer | None = None
    visualization_context: Optional[VisualizationContext] = None
    live_renderer: Optional[LiveTaskStatusRenderer] = None
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as http_client:
        try:
            if api_url is None:
                local_server = LocalAPIServer(extra_cli_args=extra_cli_args)
                base_url = local_server.start()
                logger.info(f"Started local mineru-api at {base_url}")
                server_health = await wait_for_local_api_ready(http_client, local_server)
                effective_max_concurrent_requests = (
                    server_health.max_concurrent_requests
                )
            else:
                server_health = await fetch_server_health(
                    http_client,
                    normalize_base_url(api_url),
                )
                effective_max_concurrent_requests = (
                    resolve_effective_max_concurrent_requests(
                        read_max_concurrent_requests(
                            default=DEFAULT_MAX_CONCURRENT_REQUESTS
                        ),
                        server_health.max_concurrent_requests,
                    )
                )
                live_renderer = create_live_task_status_renderer(api_url)

            planned_tasks = plan_tasks(
                documents=documents,
                backend=backend,
                processing_window_size=server_health.processing_window_size
                if backend == "pipeline"
                else DEFAULT_PROCESSING_WINDOW_SIZE,
            )
            progress = build_task_execution_progress(planned_tasks)
            concurrency = resolve_submit_concurrency(
                effective_max_concurrent_requests,
                len(planned_tasks),
            )
            form_data = build_request_form_data(
                lang=lang,
                backend=backend,
                method=method,
                formula_enable=formula_enable,
                table_enable=table_enable,
                server_url=server_url,
                start_page_id=start_page_id,
                end_page_id=end_page_id,
            )
            visualization_context = create_visualization_context()
            failures = await execute_planned_tasks(
                planned_tasks=planned_tasks,
                concurrency=concurrency,
                task_runner=lambda planned_task: run_planned_task(
                    client=http_client,
                    server_health=server_health,
                    planned_task=planned_task,
                    progress=progress,
                    backend=backend,
                    parse_method=method,
                    visualization_context=visualization_context,
                    form_data=form_data,
                    output_dir=output_dir,
                    live_renderer=live_renderer,
                ),
            )
            if failures:
                details = "\n".join(
                    f"- task#{failure.task_index} ({', '.join(failure.document_stems)}): {failure.message}"
                    for failure in sorted(failures, key=lambda item: item.task_index)
                )
                raise click.ClickException(
                    f"{len(failures)} task(s) failed while processing documents:\n{details}"
                )
        finally:
            try:
                if local_server is not None:
                    local_server.stop()
            finally:
                try:
                    await wait_for_visualization_jobs(visualization_context)
                finally:
                    if live_renderer is not None:
                        live_renderer.close()
                        _stderr_sink.set_renderer(None)