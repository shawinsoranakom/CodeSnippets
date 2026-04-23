def _parse_late_interaction_meta(
        pooling_params: PoolingParams | None,
    ) -> tuple[str | None, str | None, int | None]:
        if pooling_params is None or pooling_params.late_interaction_params is None:
            return None, None, None

        late_interaction_params = pooling_params.late_interaction_params
        mode = late_interaction_params.mode

        query_key = late_interaction_params.query_key
        if not isinstance(query_key, str) or not query_key:
            raise ValueError(
                "late-interaction request is missing a valid query key in "
                "pooling_params.late_interaction_params."
            )

        if mode == LATE_INTERACTION_MODE_CACHE_QUERY:
            query_uses_raw = late_interaction_params.query_uses
            if query_uses_raw is None:
                query_uses_raw = 1
            try:
                query_uses = max(1, int(query_uses_raw))
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "late-interaction query uses must be an integer value."
                ) from exc
            return mode, query_key, query_uses

        return mode, query_key, None