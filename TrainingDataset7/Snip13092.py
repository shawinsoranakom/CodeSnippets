def using(
        self,
        *,
        priority=None,
        queue_name=None,
        run_after=None,
        backend=None,
    ):
        """Create a new Task with modified defaults."""

        changes = {}
        if priority is not None:
            changes["priority"] = priority
        if queue_name is not None:
            changes["queue_name"] = queue_name
        if run_after is not None:
            changes["run_after"] = run_after
        if backend is not None:
            changes["backend"] = backend
        return replace(self, **changes)