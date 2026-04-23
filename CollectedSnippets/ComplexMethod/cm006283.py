def topological_sort_spans(
    resolved: list[tuple[dict[str, Any], UUID, UUID | None]],
) -> list[tuple[dict[str, Any], UUID, UUID | None]]:
    """Sort spans so parents appear before children.

    PostgreSQL enforces foreign-key constraints at INSERT time, so a child
    span referencing ``parent_span_id`` will fail if the parent row hasn't
    been written yet.  This performs a Kahn's-algorithm-style topological
    sort over the batch so that every parent is inserted first.

    Spans whose ``parent_span_id`` points outside the current batch are
    treated as roots (the parent already exists in the DB from a prior
    flush).
    """
    batch_ids = {span_uuid for _, span_uuid, _ in resolved}

    sorted_spans: list[tuple[dict[str, Any], UUID, UUID | None]] = []
    inserted: set[UUID] = set()
    remaining = list(resolved)

    while remaining:
        next_round: list[tuple[dict[str, Any], UUID, UUID | None]] = []
        progress = False
        for item in remaining:
            _, span_uuid, parent_uuid = item
            # Insert if: no parent, parent outside batch, or parent already inserted
            if parent_uuid is None or parent_uuid not in batch_ids or parent_uuid in inserted:
                sorted_spans.append(item)
                inserted.add(span_uuid)
                progress = True
            else:
                next_round.append(item)

        if not progress:
            # Cycle or unresolvable dependency detected.
            # To avoid reintroducing foreign-key violations, break the cycle by
            # nulling out parent_span_id for the remaining spans before inserting.
            if next_round:
                logger.warning(
                    "Detected cycle or unresolvable span dependencies in tracing batch; "
                    "breaking parent relationships for %d spans to preserve DB integrity.",
                    len(next_round),
                )
            for span_data, span_uuid, _parent_uuid in next_round:
                # Append with a nulled parent — do NOT mutate the original span_data
                # dict because callers may still reference it after the sort.
                sorted_spans.append((span_data, span_uuid, None))
            break
        remaining = next_round

    return sorted_spans