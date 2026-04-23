def _fetch_parent_user_ids(
        self,
        session: Session,
        rows: list[Row],
        max_bind_vars: int,
    ) -> dict[bytes, bytes] | None:
        """Resolve parent-context user_ids for rows in a filtered query.

        Done in Python rather than as a SQL union branch because the
        context_parent_id_bin column is sparsely populated — scanning the
        States table for non-null parents costs ~40% of the overall query
        on real datasets. Here we collect only the parent ids we actually
        need and fetch them via an indexed point-lookup on context_id_bin.
        """
        cache = self.logbook_run.context_user_ids
        pending: set[bytes] = {
            parent_id
            for row in rows
            if (parent_id := row[CONTEXT_PARENT_ID_BIN_POS]) and parent_id not in cache
        }
        if not pending:
            return None
        query_parent_user_ids: dict[bytes, bytes] = {}
        # The lambda statement unions events and states, so each id appears
        # in two IN clauses — halve the chunk size to stay under the
        # database's max bind variable count.
        for pending_chunk in chunked_or_all(pending, max_bind_vars // 2):
            # Schema allows NULL but the query's WHERE clauses exclude it;
            # explicit checks satisfy the type checker.
            query_parent_user_ids.update(
                {
                    parent_id: user_id
                    for parent_id, user_id in execute_stmt_lambda_element(
                        session,
                        select_context_user_ids_for_context_ids(pending_chunk),
                        orm_rows=False,
                    )
                    if parent_id is not None and user_id is not None
                }
            )
        if self.logbook_run.for_live_stream:
            cache.update(query_parent_user_ids)
        return query_parent_user_ids