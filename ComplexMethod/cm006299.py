async def fetch_traces(
    user_id: UUID,
    flow_id: UUID | None,
    session_id: str | None,
    status: SpanStatus | None,
    query: str | None,
    start_time: datetime | None,
    end_time: datetime | None,
    page: int,
    size: int,
) -> TraceListResponse:
    """Fetch a paginated list of traces for a user, with optional filters."""
    try:
        async with session_scope() as session:
            stmt = (
                select(TraceTable)
                .join(Flow, col(TraceTable.flow_id) == col(Flow.id))
                .where(col(Flow.user_id) == user_id)
            )
            count_stmt = (
                select(func.count())
                .select_from(TraceTable)
                .join(Flow, col(TraceTable.flow_id) == col(Flow.id))
                .where(col(Flow.user_id) == user_id)
            )

            # Build filter expressions once and apply them to both statements,
            # avoiding the duplication of every condition across stmt + count_stmt.
            filters: list[Any] = []
            if flow_id:
                filters.append(TraceTable.flow_id == flow_id)
            if session_id:
                filters.append(TraceTable.session_id == session_id)
            if status:
                filters.append(TraceTable.status == status)
            if query:
                search_value = f"%{query}%"
                filters.append(
                    sa.or_(
                        sa.cast(TraceTable.name, sa.String).ilike(search_value),
                        sa.cast(TraceTable.id, sa.String).ilike(search_value),
                        sa.cast(TraceTable.session_id, sa.String).ilike(search_value),
                    )
                )
            if start_time:
                filters.append(TraceTable.start_time >= start_time)
            if end_time:
                filters.append(TraceTable.start_time <= end_time)

            for f in filters:
                stmt = stmt.where(f)
                count_stmt = count_stmt.where(f)

            stmt = stmt.order_by(col(TraceTable.start_time).desc())
            stmt = stmt.offset((page - 1) * size).limit(size)

            total = (await session.exec(count_stmt)).one()
            traces = (await session.exec(stmt)).all()

            trace_ids = [trace.id for trace in traces]
            summary_map = await fetch_trace_summary_data(session, trace_ids)

            total_count = int(total)
            total_pages = math.ceil(total_count / size) if total_count > 0 else 0
            trace_summaries = []
            for trace in traces:
                summary = summary_map.get(str(trace.id))
                effective_tokens = summary.total_tokens if summary else trace.total_tokens
                trace_summaries.append(
                    TraceSummaryRead(
                        **_trace_to_base_fields(trace, effective_tokens, summary),
                    )
                )

            return TraceListResponse(
                traces=trace_summaries,
                total=total_count,
                pages=total_pages,
            )
    except Exception:
        logger.exception("Error fetching traces")
        raise