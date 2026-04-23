def sample(
        self,
        tokenizer: TokenizerLike,
        num_requests: int,
        request_id_prefix: str = "",
        no_oversample: bool = False,
        prefix_len: int = RandomDataset.DEFAULT_PREFIX_LEN,
        range_ratio: RangeRatio = RandomDataset.DEFAULT_RANGE_RATIO,
        input_len: int = RandomDataset.DEFAULT_INPUT_LEN,
        output_len: int = RandomDataset.DEFAULT_OUTPUT_LEN,
        batchsize: int = 1,
        limit_mm_per_prompt: dict[str, int] = DEFAULT_LIMIT_MM_PER_PROMPT,
        base_items_per_request: int = DEFAULT_BASE_ITEMS_PER_REQUEST,
        num_mm_items_range_ratio: float = DEFAULT_NUM_MM_ITEMS_RANGE_RATIO,
        bucket_config: dict[
            tuple[int, int, int], float
        ] = DEFAULT_MM_ITEM_BUCKET_CONFIG,
        enable_multimodal_chat: bool = DEFAULT_ENABLE_MULTIMODAL_CHAT,
        **kwargs,
    ) -> list[SampleRequest]:
        if batchsize != 1:
            raise NotImplementedError(
                "batchsize > 1 is not supported for RandomMultiModalDataset."
            )

        input_lens, output_lens, offsets = get_sampling_params(
            self._rng,
            num_requests,
            range_ratio,
            input_len,
            output_len,
            tokenizer,
        )

        (
            min_num_mm_items,
            max_num_mm_items,
            limit_mm_per_prompt,
            bucket_config,
        ) = self.get_mm_item_sampling_params(
            base_items_per_request,
            num_mm_items_range_ratio,
            limit_mm_per_prompt,
            bucket_config,
        )

        vocab_size = tokenizer.vocab_size
        # Can't use tokenizer.all_special_ids since
        # it returns ONLY ids from special_tokens_map.json
        # We want to exclude placeholder tokens and all
        # tokens that indicate start/end of image as it
        # may break prompt replacement logic.
        prohibited_tokens = list(
            tok_id
            for tok_id, token in tokenizer.added_tokens_decoder.items()
            if token.special
        )
        all_tokens = np.arange(vocab_size)
        allowed_tokens = np.array(list(set(all_tokens) - set(prohibited_tokens)))
        logger.debug(
            "Sampling from %d out of %d (vocab size)", len(allowed_tokens), vocab_size
        )
        # Generate prefix once
        prefix_token_ids = self.get_prefix(tokenizer, allowed_tokens, prefix_len)
        # Add synthetic multimodal items to each request
        mm_requests = []
        token_mismatch_total = 0
        for i in range(num_requests):
            prompt, total_input_len, token_mismatch = self.generate_token_sequence(  # noqa: E501
                tokenizer=tokenizer,
                prefix_token_ids=prefix_token_ids,
                prefix_len=prefix_len,
                vocab_size=vocab_size,
                input_len=int(input_lens[i]),
                offset=int(offsets[i]),
                index=i,
                allowed_tokens=allowed_tokens,
            )
            token_mismatch_total += token_mismatch
            # Get multimodal item iterator for a given request
            mm_item_iterator = self.get_mm_item_iterator(
                min_num_mm_items,
                max_num_mm_items,
                bucket_config,
                limit_mm_per_prompt,
            )

            mm_content = cast(
                list[dict[str, Any]],
                [
                    self.generate_mm_item(mm_item_config)
                    for mm_item_config in mm_item_iterator
                ],
            )

            if enable_multimodal_chat:
                # NOTE: For now this option is only provided for completeness
                # given that the serve.py benchmark currently does not use it.
                mm_chat_prompt: Any = prompt
                mm_chat_prompt = self.apply_multimodal_chat_transformation(
                    prompt, mm_content
                )
                sample_request = SampleRequest(
                    prompt=mm_chat_prompt,
                    prompt_len=total_input_len,
                    expected_output_len=int(output_lens[i]),
                    multi_modal_data=None,
                    request_id=request_id_prefix + str(i),
                )
            else:
                sample_request = SampleRequest(
                    prompt=prompt,
                    prompt_len=total_input_len,
                    expected_output_len=int(output_lens[i]),
                    multi_modal_data=mm_content,
                    request_id=request_id_prefix + str(i),
                )
            mm_requests.append(sample_request)

        if token_mismatch_total != 0:
            sign = "more" if token_mismatch_total > 0 else "fewer"
            logger.warning(
                "Across all generated prompts, there were %d %s tokens "
                "than expected after decoding and re-encoding. This is "
                "expected due to the imperfect nature of the sampling "
                "procedure.",
                abs(token_mismatch_total),
                sign,
            )

        return mm_requests