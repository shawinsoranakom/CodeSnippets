def sample(
        self,
        tokenizer: TokenizerLike,
        num_requests: int,
        request_id_prefix: str = "",
        no_oversample: bool = False,
        prefix_len: int = DEFAULT_PREFIX_LEN,
        range_ratio: RangeRatio = DEFAULT_RANGE_RATIO,
        input_len: int = DEFAULT_INPUT_LEN,
        output_len: int = DEFAULT_OUTPUT_LEN,
        batchsize: int = 1,
        max_loras: int | None = None,
        lora_path: str | None = None,
        lora_assignment: str = "random",
        **kwargs,
    ) -> list[SampleRequest]:
        resolved_input_rr, _ = _resolve_range_ratios(range_ratio)

        num_special = int(tokenizer.num_special_tokens_to_add())
        real_input_len = max(0, int(input_len) - num_special)
        min_sampled_input = math.floor(
            real_input_len * (1.0 - float(resolved_input_rr))
        )
        min_total_input = int(prefix_len) + min_sampled_input
        if min_total_input < 1:
            raise ValueError(
                "--random-input-len is too small: with tokenizer special "
                f"tokens {num_special} and "
                f"input range ratio {resolved_input_rr}, "
                "the minimum possible total input tokens (prefix + sampled) is "
                f"{min_total_input}. Increase --random-input-len and/or "
                "--random-prefix-len, or decrease the input range ratio "
                "so that prefix_len + floor(max(0, random_input_len - "
                "num_special)) * (1 - input_range_ratio) >= 1."
            )

        input_lens, output_lens, offsets = get_sampling_params(
            self._rng,
            num_requests,
            range_ratio,
            input_len,
            output_len,
            tokenizer,
        )

        vocab_size = tokenizer.vocab_size
        prohibited_tokens = tokenizer.all_special_ids
        all_tokens = np.arange(vocab_size)
        allowed_tokens = np.array(list(set(all_tokens) - set(prohibited_tokens)))

        # Generate prefix once
        prefix_token_ids = self.get_prefix(tokenizer, allowed_tokens, prefix_len)

        requests = []
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
            lora_req = self.get_lora_request(
                index=i,
                max_loras=max_loras,
                lora_path=lora_path,
                lora_assignment=lora_assignment,
            )
            requests.append(
                SampleRequest(
                    prompt=prompt,
                    prompt_len=total_input_len,
                    expected_output_len=int(output_lens[i]),
                    lora_request=lora_req,
                    request_id=request_id_prefix + str(i),
                )
            )
        # only used for embeddings benchmark.
        if batchsize > 1:
            batch_requests = []
            # Create batched requests
            for i in range(0, num_requests, batchsize):
                batch = requests[i : i + batchsize]
                batch_requests.append(
                    SampleRequest(
                        prompt=[req.prompt for req in batch],
                        prompt_len=sum(req.prompt_len for req in batch),
                        expected_output_len=0,
                        request_id=request_id_prefix + str(i // batchsize),
                    )
                )
            requests = batch_requests

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

        return requests