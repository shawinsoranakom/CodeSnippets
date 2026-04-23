def end_trace(
        self,
        trace_id: str,
        trace_name: str,
        outputs: dict[str, Any] | None = None,
        error: Exception | None = None,
        logs: Sequence[Log | dict] = (),
    ) -> None:
        """End a component-level trace span.

        Args:
            trace_id: Component ID
            trace_name: Component name
            outputs: Output data
            error: Optional error
            logs: Optional logs
        """
        if not self._ready:
            return

        end_time = datetime.now(tz=timezone.utc)

        span_info = self.spans.pop(trace_id, None)
        if not span_info:
            return

        start_time = span_info["start_time"]
        latency_ms = int((end_time - start_time).total_seconds() * 1000)

        # Merge outputs, error, and logs into one dict so the DB stores a single JSON blob per span.
        output_data: dict[str, Any] = {}
        if outputs:
            output_data.update(outputs)
        if error:
            output_data["error"] = str(error)
        if logs:
            output_data["logs"] = [log if isinstance(log, dict) else log.model_dump() for log in logs]

        # Pop so tokens aren't double-counted if end_trace is called more than once for the same component.
        tokens = self._component_tokens.pop(trace_id, {})

        # Use OTel GenAI conventions so observability tools can parse token usage uniformly across providers
        attributes: dict[str, Any] = {}
        if tokens.get("gen_ai.usage.input_tokens"):
            attributes["gen_ai.usage.input_tokens"] = tokens["gen_ai.usage.input_tokens"]
        if tokens.get("gen_ai.usage.output_tokens"):
            attributes["gen_ai.usage.output_tokens"] = tokens["gen_ai.usage.output_tokens"]

        self.completed_spans.append(
            self._build_completed_span(
                span_id=trace_id,
                name=span_info["name"],
                span_type=self._map_trace_type(span_info["trace_type"]),
                inputs=span_info["inputs"],
                outputs=serialize(output_data) if output_data else None,
                start_time=start_time,
                end_time=end_time,
                latency_ms=latency_ms,
                error=str(error) if error else None,
                attributes=attributes,
                span_source="component",
            )
        )

        # Reset so the next component's LangChain spans don't inherit this component as parent.
        self._current_component_id = None