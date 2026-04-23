async def submit_router_task(
    request: Request,
    payload: MultipartPayload,
) -> RouterTaskRecord:
    validate_public_http_client_request(
        public_bind_exposed=bool(
            getattr(request.app.state, "public_bind_exposed", False)
        ),
        allow_public_http_client=bool(
            getattr(request.app.state, "allow_public_http_client", False)
        ),
        backend=payload.get_field_value("backend") or "",
        server_url=payload.get_field_value("server_url"),
    )
    worker_pool: WorkerPool = request.app.state.worker_pool
    registry: RouterTaskRegistry = request.app.state.router_task_registry
    attempted_servers: set[str] = set()
    last_error: str | None = None

    while True:
        server = await worker_pool.acquire_submission_server(excluded_server_ids=attempted_servers)
        if server is None:
            if last_error is None:
                raise HTTPException(status_code=503, detail="No healthy upstream MinerU API servers are available")
            raise HTTPException(status_code=503, detail=last_error)

        try:
            upstream_payload = await submit_payload_to_upstream(server.base_url, payload)
            file_names = upstream_payload["file_names"]
            normalized_file_names = (
                list(file_names)
                if isinstance(file_names, list) and all(isinstance(item, str) for item in file_names)
                else []
            )
            return await registry.register(
                upstream_server_id=server.server_id,
                upstream_base_url=server.base_url,
                upstream_task_id=upstream_payload["task_id"],
                backend=upstream_payload["backend"],
                file_names=normalized_file_names,
                created_at=upstream_payload["created_at"],
                status=upstream_payload["status"],
                started_at=upstream_payload["started_at"] if isinstance(upstream_payload["started_at"], str) else None,
                completed_at=upstream_payload["completed_at"] if isinstance(upstream_payload["completed_at"], str) else None,
                error=upstream_payload["error"] if isinstance(upstream_payload["error"], str) else None,
                queued_ahead=upstream_payload["queued_ahead"],
            )
        except UpstreamSubmissionRejected as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
        except UpstreamSubmissionUnavailable as exc:
            attempted_servers.add(server.server_id)
            last_error = f"Failed to submit task via {server.server_id}: {exc}"
            await worker_pool.mark_submission_failure(server.server_id, str(exc))
        finally:
            await worker_pool.release_submission_server(server.server_id)