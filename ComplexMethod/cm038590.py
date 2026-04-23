async def create_generative_scoring(
        self,
        request: GenerativeScoringRequest,
        raw_request: Request | None = None,
    ) -> GenerativeScoringResponse | ErrorResponse:
        """Create generative scoring for the given request.

        Args:
            request: The GenerativeScoringRequest containing query, items, and
                label_token_ids.
            raw_request: The raw FastAPI request object.

        Returns:
            GenerativeScoringResponse with probabilities for each item, or
            ErrorResponse if an error occurred.
        """
        # Check model
        error_check_ret = await self._check_model(request)  # type: ignore[arg-type]
        if error_check_ret is not None:
            return error_check_ret

        # Check if engine is alive
        if self.engine_client.errored:
            raise self.engine_client.dead_error

        # Get tokenizer
        tokenizer = self.renderer.tokenizer
        if tokenizer is None:
            return self.create_error_response(
                "Tokenizer not available. Cannot process generative scoring request."
            )

        # Validate label_token_ids
        vocab_size = self.model_config.get_vocab_size()
        for token_id in request.label_token_ids:
            if token_id < 0 or token_id >= vocab_size:
                return self.create_error_response(
                    f"label_token_id {token_id} is out of vocabulary range "
                    f"[0, {vocab_size}). Please provide valid token IDs."
                )

        if len(request.label_token_ids) == 0:
            return self.create_error_response(
                "label_token_ids must contain at least one token ID."
            )

        # Validate items
        if len(request.items) == 0:
            return self.create_error_response("items must contain at least one item.")

        # Note: Mixed item types (string and token list) are validated by
        # Pydantic at request parsing time, so we don't need to check here.

        try:
            lora_request = self._maybe_get_adapters(request)  # type: ignore[arg-type]
        except (ValueError, TypeError, RuntimeError) as e:
            logger.exception("Error preparing request components")
            return self.create_error_response(e)

        base_id = self._base_request_id(raw_request, default=request.request_id)
        request_id = f"generative-scoring-{base_id}"
        created_time = int(time.time())

        # Build prompts for each item
        try:
            engine_inputs, prompt_token_counts = await self._build_prompts(
                request, tokenizer, self.model_config.max_model_len
            )
        except (ValueError, TypeError) as e:
            logger.exception("Error building prompts")
            return self.create_error_response(e)

        # Create sampling params for scoring
        # We use max_tokens=1 with logprob_token_ids to efficiently get
        # logprobs for only the specified label tokens (not full vocab)
        # Note: temperature/top_k/top_p don't affect logprobs - they only
        # affect the sampling distribution. Logprobs are computed from raw
        # logits via log_softmax before any sampling transformations.
        sampling_params = SamplingParams(
            max_tokens=1,
            logprobs=len(request.label_token_ids),
            logprob_token_ids=request.label_token_ids,
            n=1,
        )

        # Get trace headers
        trace_headers = (
            None
            if raw_request is None
            else await self._get_trace_headers(raw_request.headers)
        )

        # Schedule requests for all inputs
        generators: list[AsyncGenerator[RequestOutput, None]] = []
        for i, engine_input in enumerate(engine_inputs):
            request_id_item = f"{request_id}-{i}"

            self._log_inputs(
                request_id_item,
                engine_input,
                params=sampling_params,
                lora_request=lora_request,
            )

            generator = self.engine_client.generate(
                engine_input,
                sampling_params,
                request_id_item,
                lora_request=lora_request,
                trace_headers=trace_headers,
                priority=request.priority,
            )
            generators.append(generator)

        # Collect results
        result_generator = merge_async_iterators(*generators)
        results: list[RequestOutput | None] = [None] * len(engine_inputs)

        try:
            async for i, res in result_generator:
                results[i] = res
        except asyncio.CancelledError:
            return self.create_error_response("Client disconnected")
        except Exception as e:
            logger.exception("Error during generation")
            return self.create_error_response(e)

        # Process results to extract label token probabilities
        item_results: list[GenerativeScoringItemResult] = []
        total_prompt_tokens = 0
        total_completion_tokens = 0

        for i, result in enumerate(results):
            if result is None:
                return self.create_error_response(
                    f"Failed to generate result for item {i}"
                )

            # Check for errors
            if result.outputs and result.outputs[0].finish_reason == "error":
                return self.create_error_response(f"Generation error for item {i}")

            # Get logprobs from the generated token
            if not result.outputs or len(result.outputs) == 0:
                return self.create_error_response(f"No output generated for item {i}")

            output = result.outputs[0]
            if output.logprobs is None or len(output.logprobs) == 0:
                return self.create_error_response(
                    f"No logprobs available for item {i}. "
                    "This might indicate an issue with logprobs configuration."
                )

            # The logprobs dict maps token_id -> Logprob object
            # For logprobs=-1, this contains all vocab tokens
            logprobs_dict = output.logprobs[0]

            # Extract logprobs for label tokens
            label_logprobs: dict[int, float] = {}
            missing_tokens = []
            for token_id in request.label_token_ids:
                if token_id in logprobs_dict:
                    label_logprobs[token_id] = logprobs_dict[token_id].logprob
                else:
                    missing_tokens.append(token_id)

            if missing_tokens:
                return self.create_error_response(
                    f"Token IDs {missing_tokens} not found in logprobs for item {i}. "
                    "This might indicate the tokens are outside the model's vocabulary."
                )

            # Compute probabilities based on apply_softmax setting
            token_probs = self._compute_probabilities(
                label_logprobs,
                apply_softmax=request.apply_softmax,
            )

            # Use the first label token's probability as the score
            first_label_id = request.label_token_ids[0]
            score = token_probs[first_label_id]

            item_results.append(
                GenerativeScoringItemResult(
                    index=i,
                    score=score,
                )
            )

            # Update token counts
            total_prompt_tokens += prompt_token_counts[i]
            total_completion_tokens += len(output.token_ids)

        # Build response
        model_name = self.models.model_name(lora_request)
        response = GenerativeScoringResponse(
            id=request_id,
            created=created_time,
            model=model_name,
            data=item_results,
            usage=UsageInfo(
                prompt_tokens=total_prompt_tokens,
                total_tokens=total_prompt_tokens + total_completion_tokens,
                completion_tokens=total_completion_tokens,
            ),
        )

        return response