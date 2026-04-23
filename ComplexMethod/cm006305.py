def add_trace(
        self,
        trace_id: str,
        trace_name: str,
        trace_type: str,
        inputs: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        vertex: Vertex | None = None,
    ) -> None:
        """Adds a trace span, attaching inputs and metadata as attributes."""
        if not self._ready:
            return

        span_context = self.propagator.extract(carrier=self.carrier)
        child_span = self.tracer.start_span(
            name=trace_name,
            context=span_context,
            start_time=self._get_current_timestamp(),
        )

        if trace_type == "prompt":
            child_span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "chain")
        else:
            child_span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, trace_type)

        processed_inputs = self._convert_to_arize_phoenix_types(inputs) if inputs else {}
        if processed_inputs:
            child_span.set_attribute(SpanAttributes.INPUT_VALUE, self._safe_json_dumps(processed_inputs))
            child_span.set_attribute(SpanAttributes.INPUT_MIME_TYPE, OpenInferenceMimeTypeValues.JSON.value)

        processed_metadata = self._convert_to_arize_phoenix_types(metadata) if metadata else {}
        if processed_metadata:
            for key, value in processed_metadata.items():
                child_span.set_attribute(f"{SpanAttributes.METADATA}.{key}", value)

        if vertex and vertex.id is not None:
            child_span.set_attribute("vertex_id", vertex.id)

        component_name = trace_id.split("-")[0]
        if component_name == "ChatInput":
            self.chat_input_value = processed_inputs["input_value"]
        elif component_name == "ChatOutput":
            self.chat_output_value = processed_inputs["input_value"]

        self.child_spans[trace_id] = child_span