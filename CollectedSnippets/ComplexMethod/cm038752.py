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
        is_reranker: bool = True,
        **kwargs,
    ) -> list[SampleRequest]:
        n_sep_tokens = int(is_reranker)

        query_len_param = (input_len // 2) - n_sep_tokens if is_reranker else input_len

        query_lens, _, query_offsets = get_sampling_params(
            self._rng,
            1,
            range_ratio,
            query_len_param,
            0,
            tokenizer,
        )

        query_len = int(query_lens[0])

        if not is_reranker:
            assert num_requests > 1 and batchsize > 1
            num_requests -= 1
            batchsize -= 1
            doc_len_param = input_len
        else:
            doc_len_param = input_len - query_len - n_sep_tokens

        doc_lens, _, doc_offsets = get_sampling_params(
            self._rng,
            num_requests,
            range_ratio,
            doc_len_param,
            0,
            tokenizer,
        )

        vocab_size = tokenizer.vocab_size
        prohibited_tokens = tokenizer.all_special_ids
        all_tokens = np.arange(vocab_size)
        allowed_tokens = np.array(list(set(all_tokens) - set(prohibited_tokens)))

        query_prompt, query_input_len, token_mismatch_total = (
            self.generate_token_sequence(
                tokenizer=tokenizer,
                prefix_token_ids=[],
                prefix_len=0,
                vocab_size=vocab_size,
                input_len=query_len,
                offset=int(query_offsets[0]),
                index=0,
                allowed_tokens=allowed_tokens,
            )
        )

        requests = []
        for i in range(num_requests):
            prompt, total_input_len, token_mismatch = self.generate_token_sequence(  # noqa: E501
                tokenizer=tokenizer,
                prefix_token_ids=[],
                prefix_len=0,
                vocab_size=vocab_size,
                input_len=int(doc_lens[i]),
                offset=int(doc_offsets[i]),
                index=i + 1,
                allowed_tokens=allowed_tokens,
            )
            token_mismatch_total += token_mismatch
            requests.append((prompt, total_input_len))

        batch_requests = []
        # Create batched requests
        for i in range(0, num_requests, batchsize):
            batch = requests[i : i + batchsize]
            query_contrib = (
                (query_input_len + n_sep_tokens) * len(batch)
                if is_reranker
                else query_input_len
            )
            batch_requests.append(
                SampleRequest(
                    prompt=[query_prompt] + [req[0] for req in batch],
                    prompt_len=query_contrib + sum(req[1] for req in batch),
                    expected_output_len=0,
                    request_id=request_id_prefix + str(i // batchsize),
                )
            )

        if token_mismatch_total != 0:
            logger.warning(
                "Across all generated prompts, there were %d %s tokens "
                "than expected after decoding and re-encoding. This is "
                "expected due to the imperfect nature of the sampling "
                "procedure.",
                abs(token_mismatch_total),
                "more" if token_mismatch_total > 0 else "fewer",
            )

        return batch_requests