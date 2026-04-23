def add_trace(
        self,
        trace_id: str,
        trace_name: str,
        trace_type: str,
        inputs: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        vertex: Vertex | None = None,
    ) -> None:
        if not self._ready:
            return
        # If user is not using session_id, then it becomes the same as flow_id, but
        # we don't want to have an infinite thread with all the flow messages
        if "session_id" in inputs and inputs["session_id"] != self.flow_id:
            self.trace.update(metadata=(self.trace.metadata or {}) | {"thread_id": inputs["session_id"]})

        name_without_id = " (".join(trace_name.split(" (")[0:-1])

        previous_nodes = (
            [span for key, span in self.spans.items() for edge in vertex.incoming_edges if key == edge.source_id]
            if vertex and len(vertex.incoming_edges) > 0
            else []
        )

        span = self.trace.span(
            # Add a nanoid to make the span_id globally unique, which is required for LangWatch for now
            span_id=f"{trace_id}-{nanoid.generate(size=6)}",
            name=name_without_id,
            type="component",
            parent=(previous_nodes[-1] if len(previous_nodes) > 0 else self.trace.root_span),
            input=self._convert_to_langwatch_types(inputs),
        )
        self.trace.set_current_span(span)
        self.spans[trace_id] = span