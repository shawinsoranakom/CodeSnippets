async def update_from_upstream_payload(
        self,
        task_id: str,
        payload: dict[str, Any],
    ) -> RouterTaskRecord | None:
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            task.status = str(payload.get("status", task.status))
            task.backend = str(payload.get("backend", task.backend))
            file_names = payload.get("file_names")
            if isinstance(file_names, list) and all(isinstance(item, str) for item in file_names):
                task.file_names = list(file_names)
            task.created_at = str(payload.get("created_at", task.created_at))
            task.started_at = payload.get("started_at") if payload.get("started_at") is None else str(payload.get("started_at"))
            task.completed_at = payload.get("completed_at") if payload.get("completed_at") is None else str(payload.get("completed_at"))
            task.error = payload.get("error") if payload.get("error") is None else str(payload.get("error"))
            queued_ahead = payload.get("queued_ahead")
            task.queued_ahead = queued_ahead if isinstance(queued_ahead, int) else None
            task.upstream_error_count = 0
            return task