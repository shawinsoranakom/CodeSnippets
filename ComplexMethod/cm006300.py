async def fetch_single_trace(user_id: UUID, trace_id: UUID) -> TraceRead | None:
    """Fetch a single trace with its full hierarchical span tree."""
    async with session_scope() as session:
        stmt = (
            select(TraceTable)
            .join(Flow, col(TraceTable.flow_id) == col(Flow.id))
            .where(col(TraceTable.id) == trace_id)
            .where(col(Flow.user_id) == user_id)
        )
        trace = (await session.exec(stmt)).first()

        if not trace:
            return None

        spans_stmt = select(SpanTable).where(SpanTable.trace_id == trace_id)
        spans_stmt = spans_stmt.order_by(col(SpanTable.start_time).asc())
        spans = (await session.exec(spans_stmt)).all()

        io_data = extract_trace_io_from_spans(list(spans))
        span_tree = build_span_tree(list(spans))

        parent_ids = {s.parent_span_id for s in spans if s.parent_span_id}
        span_ids = [s.id for s in spans]
        attributes_by_id = {s.id: (s.attributes or {}) for s in spans}
        computed_tokens = compute_leaf_token_total(span_ids, parent_ids, attributes_by_id)

        effective_tokens = computed_tokens or trace.total_tokens

        # Build a lightweight summary so _trace_to_base_fields can supply io_data.
        io_summary = TraceSummaryData(
            total_tokens=effective_tokens,
            input=io_data.get("input"),
            output=io_data.get("output"),
        )

        return TraceRead(
            **_trace_to_base_fields(trace, effective_tokens, io_summary),
            end_time=trace.end_time,
            spans=span_tree,
        )