def _make_sampling_metadata(self) -> SamplingMetadata:
        num_reqs = self.num_reqs
        if not self.all_greedy:
            temperature = copy_slice(
                self.temperature_cpu_tensor, self.temperature, num_reqs
            )
        else:
            temperature = None
        if not self.no_top_p:
            copy_slice(self.top_p_cpu_tensor, self.top_p, num_reqs)
        if not self.no_top_k:
            copy_slice(self.top_k_cpu_tensor, self.top_k, num_reqs)

        if not self.no_penalties:
            # Since syncing these tensors is expensive only copy them
            # if necessary i.e. if there are requests which require
            # penalties to be applied during sampling.
            copy_slice(
                self.frequency_penalties_cpu_tensor, self.frequency_penalties, num_reqs
            )
            copy_slice(
                self.presence_penalties_cpu_tensor, self.presence_penalties, num_reqs
            )
            copy_slice(
                self.repetition_penalties_cpu_tensor,
                self.repetition_penalties,
                num_reqs,
            )

        needs_prompt_token_ids = (
            not self.no_penalties
            or self.logits_processing_needs_token_ids[:num_reqs].any()
        )
        # The prompt tokens are used only for applying penalties or
        # step pooling during the sampling/pooling process.
        # Hence copy these tensors only when there are requests which
        # need penalties/step_pooler to be applied.
        prompt_token_ids_cpu = (
            self._make_prompt_token_ids_cpu_tensor() if needs_prompt_token_ids else None
        )
        prompt_token_ids = (
            prompt_token_ids_cpu.to(device=self.device, non_blocking=True)
            if prompt_token_ids_cpu is not None
            else None
        )

        # Only set output_token_ids if required by the current requests'
        # sampling parameters.
        needs_output_token_ids = (
            not self.no_penalties
            or bool(self.bad_words_token_ids)
            or self.logitsprocs_need_output_token_ids
        )
        output_token_ids = (
            cast(list[list[int]], self.req_output_token_ids)
            if needs_output_token_ids
            else []
        )

        allowed_token_ids_mask: torch.Tensor | None = None
        if not self.no_allowed_token_ids:
            assert self.allowed_token_ids_mask is not None
            copy_slice(
                self.allowed_token_ids_mask_cpu_tensor,
                self.allowed_token_ids_mask,
                num_reqs,
            )
            allowed_token_ids_mask = self.allowed_token_ids_mask[:num_reqs]

        # Build per-request logprob_token_ids mapping: req_index -> token_ids
        logprob_token_ids_by_index: dict[int, list[int]] | None = None
        if self.logprob_token_ids:
            logprob_token_ids_by_index = {}
            for req_id, token_ids in self.logprob_token_ids.items():
                if req_id in self.req_id_to_index:
                    req_index = self.req_id_to_index[req_id]
                    logprob_token_ids_by_index[req_index] = token_ids

        return SamplingMetadata(
            temperature=temperature,
            all_greedy=self.all_greedy,
            all_random=self.all_random,
            top_p=None if self.no_top_p else self.top_p[:num_reqs],
            top_k=None if self.no_top_k else self.top_k[:num_reqs],
            generators=self.generators,
            max_num_logprobs=self.max_num_logprobs,
            logprob_token_ids=logprob_token_ids_by_index,
            prompt_token_ids=prompt_token_ids,
            frequency_penalties=self.frequency_penalties[:num_reqs],
            presence_penalties=self.presence_penalties[:num_reqs],
            repetition_penalties=self.repetition_penalties[:num_reqs],
            output_token_ids=output_token_ids,
            spec_token_ids=self.spec_token_ids,
            no_penalties=self.no_penalties,
            allowed_token_ids_mask=allowed_token_ids_mask,
            bad_words_token_ids=self.bad_words_token_ids,
            logitsprocs=self.logitsprocs,
        )