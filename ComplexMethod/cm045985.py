def parse_submit_response(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("MinerU upstream returned an invalid submit payload")
    task_id = payload.get("task_id")
    status = payload.get("status")
    backend = payload.get("backend")
    created_at = payload.get("created_at")
    if not isinstance(task_id, str) or not isinstance(status, str) or not isinstance(backend, str):
        raise ValueError("MinerU upstream returned an invalid submit payload")
    if created_at is not None and not isinstance(created_at, str):
        raise ValueError("MinerU upstream returned an invalid submit payload")
    return {
        "task_id": task_id,
        "status": status,
        "backend": backend,
        "file_names": payload.get("file_names", []),
        "created_at": created_at or utc_now_iso(),
        "started_at": payload.get("started_at"),
        "completed_at": payload.get("completed_at"),
        "error": payload.get("error"),
        "queued_ahead": payload.get("queued_ahead") if isinstance(payload.get("queued_ahead"), int) else None,
    }