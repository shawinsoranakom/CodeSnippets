def span_to_response(span: SpanTable) -> SpanReadResponse:
    """Convert a SpanTable record to a SpanReadResponse.

    Args:
        span: SpanTable record from the database.

    Returns:
        SpanReadResponse with frontend-compatible (camelCase) field names.
    """
    token_usage = None
    if span.attributes:
        # OTel GenAI conventions enable consistent parsing across different LLM providers
        input_tokens = span.attributes.get("gen_ai.usage.input_tokens", 0)
        output_tokens = span.attributes.get("gen_ai.usage.output_tokens", 0)
        # OTel spec requires deriving total from input+output (no standard total_tokens key)
        total_tokens = safe_int_tokens(input_tokens) + safe_int_tokens(output_tokens)

        token_usage = {
            "promptTokens": safe_int_tokens(input_tokens),
            "completionTokens": safe_int_tokens(output_tokens),
            "totalTokens": total_tokens,
        }
    inputs = span.inputs if isinstance(span.inputs, dict) or span.inputs is None else {"input": span.inputs}
    outputs = span.outputs if isinstance(span.outputs, dict) or span.outputs is None else {"output": span.outputs}

    return SpanReadResponse(
        id=span.id,
        name=span.name,
        type=span.span_type or SpanType.CHAIN,
        status=span.status or SpanStatus.UNSET,
        start_time=span.start_time,
        end_time=span.end_time,
        latency_ms=span.latency_ms,
        inputs=inputs,
        outputs=outputs,
        error=span.error,
        model_name=(span.attributes or {}).get("gen_ai.response.model"),
        token_usage=token_usage,
    )