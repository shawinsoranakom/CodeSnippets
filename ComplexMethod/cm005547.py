def get_candidates(self, input_ids: torch.LongTensor) -> tuple[torch.LongTensor, torch.FloatTensor]:
        """
        Fetches the candidates to be tried for the current input.

        Args:
            input_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`):
                Indices of input sequence tokens in the vocabulary. [What are input IDs?](../glossary#input-ids)

        Return:
            `torch.LongTensor` of shape `(num_candidates, candidate_length)`: The candidate sequences to be tried.
        """
        bsz, input_length = input_ids.shape

        # Don't generate more than `max_length - 1` candidates since the target model generates one extra token.
        if self.max_length == input_length + 1:
            return input_ids, None

        chosen_ids = None
        match_found = False
        for ngram_size in range(min(self.max_matching_ngram_size, input_length - 1), 0, -1):
            # Create sliding windows of size ngram_size
            windows = input_ids.unfold(dimension=1, size=ngram_size, step=1)

            # Convert ngram to a tensor for comparison
            ngram_tensor = input_ids[0, -ngram_size:]

            # Find where the windows match the ngram
            matches = (windows == ngram_tensor).all(dim=2)

            # Get the indices of matches
            match_indices = matches.nonzero(as_tuple=True)[1]

            # Iterate through match indices to find a valid continuation
            # TODO (joao): this finds the first valid candidates (left to right), but perhaps we should find the
            # longest valid candidates?
            for idx in match_indices:
                start_idx = idx + ngram_size
                end_idx = start_idx + self.num_output_tokens
                end_idx = min(end_idx, input_length, self.max_length)

                if start_idx < end_idx:
                    chosen_ids = input_ids[0, start_idx:end_idx]

                    # Check if the each new candidate token is forbidden according to the logits processor. If all
                    # tokens are allowed, we keep `chosen_ids` as is.
                    # 1. create random logits.
                    # 2. apply the logits processor to get output logits for the next token, using the arbitrary
                    #    logits as input.
                    # 3. compare the output logits with the next candidate token. If they are -inf, then the next
                    #    candidate token is forbidden and we don't want to generate it.
                    if self.logits_processor is not None:
                        sequence_with_candidate = input_ids
                        fake_input_logits = torch.ones(
                            (bsz, self.vocab_size), device=input_ids.device, dtype=torch.float32
                        )
                        for candidate_idx, new_candidate_token in enumerate(chosen_ids):
                            fake_output_logits = self.logits_processor(sequence_with_candidate, fake_input_logits)
                            fake_candidate_logits = fake_output_logits[0, new_candidate_token]
                            # next candidate token is forbidden -> crop chosen_ids accordingly
                            if fake_candidate_logits in (-float("Inf"), torch.finfo(fake_candidate_logits.dtype).min):
                                chosen_ids = chosen_ids[:candidate_idx]
                                break
                            else:
                                sequence_with_candidate = torch.cat(
                                    (input_ids, chosen_ids[: candidate_idx + 1].unsqueeze(0)), dim=1
                                )
                        # no valid candidate tokens -> look for a different match
                        if chosen_ids.shape[0] == 0:
                            continue

                    match_found = True

                    # remove remaining candidate ids if an "eos" token is found, otherwise the target model may
                    # accept eos and the rest as valid, thus not stopping generation after "eos"
                    # NOTE: below code is written based on the fact that assisted decoding supports only bs=1
                    mask = torch.isin(chosen_ids, self.eos_token_id)
                    match_indices_eos = torch.nonzero(mask)
                    if match_indices_eos.numel() > 0:
                        first_eos_index = match_indices_eos[0].item()
                        chosen_ids = chosen_ids[:first_eos_index]
                    break
            if match_found:
                break

        # In case we didn't find a match return the input sequence unchanged, reverts back to autoregressive decoding
        if not match_found or chosen_ids is None or len(chosen_ids) == 0:
            return input_ids, None

        # Now need extend input_ids with chosen_ids
        chosen_ids = chosen_ids.unsqueeze(0)
        candidate_input_ids = torch.cat((input_ids, chosen_ids), dim=1)
        # assisted_generation expects logits as well, but we don't have those here, so returning None
        return candidate_input_ids, None