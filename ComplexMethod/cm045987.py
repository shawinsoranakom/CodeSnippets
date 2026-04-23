async def fetch_router_task_status(
    request: Request,
    task: RouterTaskRecord,
) -> RouterTaskRecord:
    if is_task_terminal(task.status):
        return task

    registry: RouterTaskRegistry = request.app.state.router_task_registry
    client: httpx.AsyncClient = request.app.state.http_client
    url = f"{task.upstream_base_url}{TASKS_ENDPOINT}/{task.upstream_task_id}"
    try:
        response = await client.get(url)
    except httpx.HTTPError as exc:
        updated = await registry.increment_upstream_error(task.task_id, str(exc))
        if updated is None:
            raise HTTPException(status_code=404, detail="Task not found") from exc
        return updated

    if response.status_code != 200:
        error = f"{response.status_code} {response_detail(response)}"
        updated = await registry.increment_upstream_error(task.task_id, error)
        if updated is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return updated

    try:
        status_payload = _parse_json_object_response(response, "task status payload")
    except ValueError as exc:
        updated = await registry.increment_upstream_error(
            task.task_id,
            f"Invalid task status payload: {exc}",
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return updated

    updated = await registry.update_from_upstream_payload(task.task_id, status_payload)
    if updated is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated