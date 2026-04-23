async def fetch_trace_summary_data(session: AsyncSession, trace_ids: list[UUID]) -> dict[str, TraceSummaryData]:
    """Fetch aggregated token totals and I/O summaries for a batch of traces.

    Makes a single database round-trip by selecting all columns needed for both
    token aggregation and I/O extraction, then processes them together per trace.

    Token counting uses only leaf spans (spans that are not parents of other spans)
    to avoid double-counting tokens in nested LLM call hierarchies.

    Args:
        session: Active async database session.
        trace_ids: List of trace IDs to aggregate.

    Returns:
        Mapping of trace ID string to :class:`TraceSummaryData`.
    """
    summary_map: dict[str, TraceSummaryData] = {}
    if not trace_ids:
        return summary_map

    all_spans_stmt = sa.select(
        col(SpanTable.trace_id),
        col(SpanTable.id),
        col(SpanTable.name),
        col(SpanTable.parent_span_id),
        col(SpanTable.end_time),
        col(SpanTable.inputs),
        col(SpanTable.outputs),
        col(SpanTable.attributes),
    ).where(col(SpanTable.trace_id).in_(trace_ids))
    rows = (await session.execute(all_spans_stmt)).all()

    parent_ids = {row[3] for row in rows if row[3] is not None}

    rows_by_trace: dict[str, list[Any]] = {}
    for row in rows:
        rows_by_trace.setdefault(str(row[0]), []).append(row)

    for trace_id_str, trace_rows in rows_by_trace.items():
        span_ids = [row[1] for row in trace_rows]
        attributes_by_id = {row[1]: (row[7] or {}) for row in trace_rows}
        total_tokens = compute_leaf_token_total(span_ids, parent_ids, attributes_by_id)

        io_rows = [(r[0], r[2], r[3], r[4], r[5], r[6]) for r in trace_rows]
        io_data = extract_trace_io_from_rows(io_rows)

        summary_map[trace_id_str] = TraceSummaryData(
            total_tokens=total_tokens,
            input=io_data.get("input"),
            output=io_data.get("output"),
        )

    return summary_map