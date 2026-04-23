def end_langchain_span(
        self,
        span_id: UUID,
        outputs: dict[str, Any] | None = None,
        error: str | None = None,
        latency_ms: int = 0,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
    ) -> None:
        """End a LangChain span (called from NativeCallbackHandler).

        Args:
            span_id: Span ID to end
            outputs: Output data
            error: Error message if failed
            latency_ms: Execution time in milliseconds
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            total_tokens: Total tokens used
        """
        if not self._ready:
            return

        span_info = self.langchain_spans.pop(span_id, None)
        if not span_info:
            return

        end_time = datetime.now(tz=timezone.utc)
        start_time = span_info["start_time"]
        actual_latency = int((end_time - start_time).total_seconds() * 1000)

        # Roll up into the component span so the UI shows per-component token totals.
        if total_tokens and self._current_component_id:
            tokens = self._component_tokens.setdefault(
                self._current_component_id,
                {
                    "gen_ai.usage.input_tokens": 0,
                    "gen_ai.usage.output_tokens": 0,
                },
            )
            tokens["gen_ai.usage.input_tokens"] += prompt_tokens or 0
            tokens["gen_ai.usage.output_tokens"] += completion_tokens or 0

        # Use OTel GenAI conventions so observability tools can parse LLM metrics uniformly
        lc_attributes: dict[str, Any] = {}
        if span_info.get("model_name"):
            # response.model captures the actual model used (vs request.model which may differ due to routing)
            lc_attributes["gen_ai.response.model"] = span_info["model_name"]
        if span_info.get("provider"):
            lc_attributes["gen_ai.provider.name"] = span_info["provider"]
        # Default to chat since most LLM usage in Langflow is conversational
        if span_info.get("span_type") == "llm":
            lc_attributes["gen_ai.operation.name"] = "chat"
        if prompt_tokens:
            lc_attributes["gen_ai.usage.input_tokens"] = prompt_tokens
        if completion_tokens:
            lc_attributes["gen_ai.usage.output_tokens"] = completion_tokens

        self.completed_spans.append(
            self._build_completed_span(
                span_id=span_info["id"],
                name=span_info["name"],
                span_type=self._map_trace_type(span_info["span_type"]),
                inputs=span_info["inputs"],
                outputs=serialize(outputs) if outputs else None,
                start_time=start_time,
                end_time=end_time,
                latency_ms=latency_ms or actual_latency,
                error=error,
                attributes=lc_attributes,
                span_source="langchain",
                parent_span_id=span_info.get("parent_span_id"),
            )
        )