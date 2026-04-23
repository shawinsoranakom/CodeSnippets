async def _flash_late_interaction_encode_queries(self, ctx: ScoringServeContext):
        assert ctx.n_queries is not None
        assert ctx.engine_inputs is not None
        assert isinstance(ctx.pooling_params, PoolingParams)

        n_queries = ctx.n_queries
        n_docs = len(ctx.engine_inputs) - n_queries
        query_engine_inputs = ctx.engine_inputs[:n_queries]

        query_keys = [f"{ctx.request_id}-query-{i}" for i in range(n_queries)]
        query_uses = [n_docs if n_queries == 1 else 1] * n_queries

        query_pooling_params_list = []
        for i in range(n_queries):
            pooling_params = ctx.pooling_params.clone()
            pooling_params.late_interaction_params = (
                build_late_interaction_query_params(
                    query_key=query_keys[i],
                    query_uses=query_uses[i],
                )
            )
            query_pooling_params_list.append(pooling_params)

        assert (
            n_queries
            == len(query_pooling_params_list)
            == len(query_engine_inputs)
            == len(query_keys)
        )

        query_ctx = ScoringServeContext(
            request=ctx.request,
            raw_request=ctx.raw_request,
            model_name=ctx.model_name,
            request_id=ctx.request_id,
            pooling_params=query_pooling_params_list,
            prompt_request_ids=query_keys,
            engine_inputs=query_engine_inputs,
        )

        await self._prepare_generators(query_ctx)
        await self._collect_batch(query_ctx)
        ctx.query_final_res_batch = query_ctx.final_res_batch