def postprocess_pooler_output(
        self,
        raw_pooler_output: PoolerOutput,
        pooling_params: list[PoolingParams],
        req_ids: list[str],
        finished_mask: list[bool],
    ) -> PoolerOutput:
        if not isinstance(raw_pooler_output, list):
            return raw_pooler_output

        num_reqs = len(pooling_params)
        if len(raw_pooler_output) != num_reqs:
            raise ValueError(
                "raw_pooler_output and pooling_params must have the same length."
            )
        if len(req_ids) != num_reqs:
            raise ValueError("req_ids and pooling_params must have the same length.")
        if len(finished_mask) != num_reqs:
            raise ValueError(
                "finished_mask and pooling_params must have the same length."
            )

        if not any(finished_mask):
            return raw_pooler_output
        if not any(p.late_interaction_params is not None for p in pooling_params):
            return raw_pooler_output

        outputs: list[torch.Tensor | None] = list(raw_pooler_output)
        score_indices: list[int] = []
        score_req_ids: list[str] = []
        score_query_keys: list[str] = []
        score_queries: list[torch.Tensor] = []
        score_docs: list[torch.Tensor] = []
        for i, (req_id, output, params, finished) in enumerate(
            zip(req_ids, outputs, pooling_params, finished_mask)
        ):
            if not finished or output is None:
                continue

            mode, query_key, query_uses = self._parse_late_interaction_meta(params)
            if mode is None:
                continue

            assert query_key is not None
            if mode == LATE_INTERACTION_MODE_CACHE_QUERY:
                assert query_uses is not None
                # `output` can be a view into the current step's hidden-states
                # buffer, so clone it before storing across scheduling steps.
                self._query_cache[query_key] = output.clone()
                self._query_uses[query_key] = query_uses
                outputs[i] = torch.zeros((), device=output.device, dtype=torch.float32)
                continue

            if mode == LATE_INTERACTION_MODE_SCORE_DOC:
                query_output = self._query_cache.get(query_key)
                if query_output is None:
                    raise ValueError(
                        "late-interaction query cache miss for key "
                        f"{query_key!r}. Ensure query requests are executed "
                        "before their paired document requests."
                    )

                score_indices.append(i)
                score_req_ids.append(req_id)
                score_query_keys.append(query_key)
                score_queries.append(query_output)
                score_docs.append(output)
                continue

            raise ValueError(f"Unsupported late-interaction mode: {mode!r}")

        if score_indices:
            score_values = compute_maxsim_score_batched(score_queries, score_docs)
            for i, req_id, query_key, score in zip(
                score_indices, score_req_ids, score_query_keys, score_values
            ):
                outputs[i] = score
                self._doc_query_keys.pop(req_id, None)
                self._release_query_use(query_key)

        return outputs