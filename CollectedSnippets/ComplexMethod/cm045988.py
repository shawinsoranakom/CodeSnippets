async def build_sync_router_task_result_response(
    request: Request,
    task: RouterTaskRecord,
) -> Response:
    client: httpx.AsyncClient = request.app.state.http_client
    result_url = f"{task.upstream_base_url}{TASKS_ENDPOINT}/{task.upstream_task_id}/result"
    try:
        upstream_response = await client.send(
            client.build_request("GET", result_url),
            stream=True,
        )
    except httpx.HTTPError as exc:
        await request.app.state.router_task_registry.increment_upstream_error(task.task_id, str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if upstream_response.status_code != 200:
        body = await upstream_response.aread()
        await upstream_response.aclose()
        detail = body.decode("utf-8", errors="replace").strip() or upstream_response.reason_phrase
        await request.app.state.router_task_registry.increment_upstream_error(
            task.task_id,
            f"{upstream_response.status_code} {detail}",
        )
        raise HTTPException(status_code=upstream_response.status_code, detail=detail)

    sync_headers = build_sync_task_headers(task, request)
    content_type = upstream_response.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            await upstream_response.aread()
            payload_data = _parse_json_object_response(
                upstream_response,
                "task result payload",
            )
        except ValueError as exc:
            detail = f"Invalid task result payload: {exc}"
            await request.app.state.router_task_registry.increment_upstream_error(
                task.task_id,
                detail,
            )
            raise HTTPException(status_code=502, detail=detail) from exc
        finally:
            await upstream_response.aclose()

        merged_payload = {
            **task.to_status_payload(request),
            "backend": payload_data.get("backend", task.backend),
            "version": payload_data.get("version", __version__),
            "results": payload_data.get("results", {}),
        }
        return JSONResponse(status_code=200, content=merged_payload, headers=sync_headers)

    headers: dict[str, str] = {}
    content_disposition = upstream_response.headers.get("content-disposition")
    if content_disposition:
        headers["content-disposition"] = content_disposition
    return StreamingResponse(
        upstream_response.aiter_bytes(),
        status_code=200,
        media_type=content_type or "application/octet-stream",
        headers={**headers, **sync_headers},
        background=BackgroundTask(upstream_response.aclose),
    )