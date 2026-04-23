async def _flash_late_interaction_encode_docs(self, ctx: ScoringServeContext):
        assert ctx.n_queries is not None
        assert ctx.engine_inputs is not None
        assert isinstance(ctx.pooling_params, PoolingParams)

        n_queries = ctx.n_queries
        n_docs = len(ctx.engine_inputs) - n_queries
        doc_engine_inputs = ctx.engine_inputs[n_queries:]

        query_keys = [f"{ctx.request_id}-query-{i}" for i in range(n_queries)]
        doc_keys = [f"{ctx.request_id}-doc-{i}" for i in range(n_docs)]

        doc_pooling_params_list = []
        for i in range(n_docs):
            query_idx = 0 if n_queries == 1 else i
            pooling_params = ctx.pooling_params.clone()
            pooling_params.late_interaction_params = build_late_interaction_doc_params(
                query_key=query_keys[query_idx]
            )
            doc_pooling_params_list.append(pooling_params)

        assert (
            n_docs
            == len(doc_pooling_params_list)
            == len(doc_engine_inputs)
            == len(doc_keys)
        )

        doc_ctx = ScoringServeContext(
            request=ctx.request,
            raw_request=ctx.raw_request,
            model_name=ctx.model_name,
            request_id=ctx.request_id,
            pooling_params=doc_pooling_params_list,
            prompt_request_ids=doc_keys,
            engine_inputs=doc_engine_inputs,
        )

        await self._prepare_generators(doc_ctx)
        await self._collect_batch(doc_ctx)

        ctx.final_res_batch = doc_ctx.final_res_batch