def end_trace(
        self,
        trace_id: str,
        trace_name: str,
        outputs: dict[str, Any] | None = None,
        error: Exception | None = None,
        logs: Sequence[Log | dict] = (),
    ) -> None:
        """Ends a trace span, attaching outputs, errors, and logs as attributes."""
        if not self._ready or trace_id not in self.child_spans:
            return

        child_span = self.child_spans[trace_id]

        processed_outputs = self._convert_to_arize_phoenix_types(outputs) if outputs else {}
        if processed_outputs:
            child_span.set_attribute(SpanAttributes.OUTPUT_VALUE, self._safe_json_dumps(processed_outputs))
            child_span.set_attribute(SpanAttributes.OUTPUT_MIME_TYPE, OpenInferenceMimeTypeValues.JSON.value)

        logs_dicts = [log if isinstance(log, dict) else log.model_dump() for log in logs]
        processed_logs = (
            self._convert_to_arize_phoenix_types({log.get("name"): log for log in logs_dicts}) if logs else {}
        )
        if processed_logs:
            child_span.set_attribute("logs", self._safe_json_dumps(processed_logs))

        self._set_span_status(child_span, error)
        child_span.end(end_time=self._get_current_timestamp())
        self.child_spans.pop(trace_id)