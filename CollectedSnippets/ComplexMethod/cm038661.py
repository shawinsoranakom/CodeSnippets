async def _prepare_generators(
        self,
        ctx: PoolingServeContext,
    ):
        if ctx.engine_inputs is None:
            raise ValueError("Engine prompts not available")

        generators: list[AsyncGenerator[PoolingRequestOutput, None]] = []

        trace_headers = (
            None
            if ctx.raw_request is None
            else await self._get_trace_headers(ctx.raw_request.headers)
        )

        assert ctx.pooling_params is not None
        pooling_params = ctx.pooling_params

        if isinstance(pooling_params, list):
            for params in pooling_params:
                params.verify(self.model_config)
        else:
            pooling_params.verify(self.model_config)

        for i, engine_input in enumerate(ctx.engine_inputs):
            prompt_request_id = (
                f"{ctx.request_id}-{i}"
                if ctx.prompt_request_ids is None
                else ctx.prompt_request_ids[i]
            )

            params = (
                pooling_params[i]
                if isinstance(pooling_params, list)
                else pooling_params
            )

            self._log_inputs(
                prompt_request_id,
                engine_input,
                params=params,
                lora_request=ctx.lora_request,
            )

            generator = self.engine_client.encode(
                engine_input,
                params,
                prompt_request_id,
                lora_request=ctx.lora_request,
                trace_headers=trace_headers,
                priority=getattr(ctx.request, "priority", 0),
            )

            generators.append(generator)

        ctx.result_generator = merge_async_iterators(*generators)