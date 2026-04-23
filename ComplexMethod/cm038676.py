async def serve_tokens(
        self,
        request: GenerateRequest,
        raw_request: Request | None = None,
    ) -> GenerateResponse | ErrorResponse | AsyncGenerator[str, None]:
        error_check_ret = await self._check_model(request)
        if error_check_ret is not None:
            logger.error("Error with model %s", error_check_ret)
            return error_check_ret

        # If the engine is dead, raise the engine's DEAD_ERROR.
        # This is required for the streaming case, where we return a
        # success status before we actually start generating text :).
        if self.engine_client.errored:
            raise self.engine_client.dead_error

        lora_request = None
        lora_request = self._maybe_get_adapters(request, supports_default_mm_loras=True)

        model_name = self.models.model_name(lora_request)

        request_id = (
            f"generate-tokens-{self._base_request_id(raw_request, request.request_id)}"
        )

        request_metadata = RequestResponseMetadata(request_id=request_id)
        if raw_request:
            raw_request.state.request_metadata = request_metadata

        engine_input: EngineInput
        if features := request.features:
            # Convert PlaceholderRangeInfo → PlaceholderRange per modality.
            mm_placeholders: dict[str, list[PlaceholderRange]] = {
                modality: [
                    PlaceholderRange(offset=p.offset, length=p.length) for p in ranges
                ]
                for modality, ranges in features.mm_placeholders.items()
            }

            # Deserialize tensor data when present; None → cache hit.
            mm_kwargs: dict[str, list[MultiModalKwargsItem | None]] = {}
            if features.kwargs_data is not None:
                for modality, items in features.kwargs_data.items():
                    mm_kwargs[modality] = [
                        decode_mm_kwargs_item(item) if item is not None else None
                        for item in items
                    ]
            else:
                for modality, hashes in features.mm_hashes.items():
                    mm_kwargs[modality] = [None] * len(hashes)

            engine_input = mm_input(
                prompt_token_ids=request.token_ids,
                mm_kwargs=MultiModalKwargsItems(mm_kwargs),
                mm_hashes=features.mm_hashes,
                mm_placeholders=mm_placeholders,
                cache_salt=request.cache_salt,
            )
        else:
            (engine_input,) = await self.openai_serving_render.preprocess_completion(
                request,
                prompt_input=request.token_ids,
                prompt_embeds=None,
                skip_mm_cache=True,
            )

        # Schedule the request and get the result generator.
        result_generator: AsyncGenerator[RequestOutput, None] | None = None
        sampling_params = request.sampling_params
        if self.force_no_detokenize:
            sampling_params.detokenize = False
        if request.stream:
            sampling_params.output_kind = RequestOutputKind.DELTA

        self._log_inputs(
            request_id,
            engine_input,
            params=sampling_params,
            lora_request=lora_request,
        )

        trace_headers = (
            None
            if raw_request is None
            else await self._get_trace_headers(raw_request.headers)
        )

        result_generator = self.engine_client.generate(
            engine_input,
            sampling_params,
            request_id,
            lora_request=lora_request,
            trace_headers=trace_headers,
            priority=request.priority,
        )

        assert result_generator is not None

        if request.stream:
            return self.serve_tokens_stream_generator(
                request,
                result_generator,
                request_id,
                model_name,
                request_metadata,
            )

        return await self.serve_tokens_full_generator(
            request, result_generator, request_id, model_name, request_metadata
        )