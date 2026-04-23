def end_trace(
        self,
        trace_id: str,
        trace_name: str,  # noqa: ARG002
        outputs: dict[str, Any] | None = None,
        error: Exception | None = None,
        logs: Sequence[Log | dict] = (),
    ):
        if not self._ready or not self._run_tree:
            return
        if trace_id not in self._children:
            logger.warning(f"Trace {trace_id} not found in children traces")
            return
        child = self._children[trace_id]
        raw_outputs = {}
        processed_outputs = {}
        if outputs:
            raw_outputs = outputs
            processed_outputs = self._convert_to_langchain_types(outputs)
        if logs:
            logs_dicts = [log if isinstance(log, dict) else log.model_dump() for log in logs]
            child.add_metadata(self._convert_to_langchain_types({"logs": {log.get("name"): log for log in logs_dicts}}))
        child.add_metadata(self._convert_to_langchain_types({"outputs": raw_outputs}))
        child.end(outputs=processed_outputs, error=self._error_to_string(error))
        self._children_traces[trace_id].__exit__(None, None, None)
        self._child_link[trace_id] = child.get_url()