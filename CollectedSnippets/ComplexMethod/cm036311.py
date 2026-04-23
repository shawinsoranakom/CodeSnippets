def get_outputs(self, num_active: int = -1) -> list[EngineCoreOutput]:
        do_logprobs = self.do_logprobs
        do_prompt_logprobs = self.do_prompt_logprobs

        outputs = []
        for req_idx, (token_ids, prompt_token_ids) in enumerate(
            zip(self.tokens_list, self.prompts_list)
        ):
            if num_active != -1 and req_idx >= num_active:
                break
            if not self.request_finished[req_idx]:
                token_idx = self.request_token_idx[req_idx]
                if do_logprobs:
                    assert self.generated_logprobs_raw is not None
                    (logprobs_token_ids_, logprobs_, sampled_token_ranks_) = (
                        self.generated_logprobs_raw[req_idx][token_idx]
                    )
                    logprobs = LogprobsLists(
                        np.array([logprobs_token_ids_]),
                        np.array([logprobs_]),
                        np.array([sampled_token_ranks_]),
                    )
                else:
                    logprobs = None
                if do_prompt_logprobs:
                    if token_idx == 0:
                        assert self.prompt_logprobs_raw is not None
                        prompt_logprobs = self.prompt_logprobs_raw[req_idx]
                    else:
                        prompt_logprobs = None
                else:
                    prompt_logprobs = None

                # Add prefill_stats on first output (prefill) for this request
                if token_idx == 0:
                    prefill_stats = PrefillStats()
                    prefill_stats.set(
                        num_prompt_tokens=len(prompt_token_ids),
                        num_local_cached_tokens=0,
                        num_external_cached_tokens=0,
                    )
                else:
                    prefill_stats = None

                new_token_id = token_ids[token_idx]
                output = EngineCoreOutput(
                    request_id=self.request_ids[req_idx],
                    new_token_ids=[new_token_id],
                    new_logprobs=logprobs,
                    new_prompt_logprobs_tensors=prompt_logprobs,
                    prefill_stats=prefill_stats,
                )
                if token_idx == len(token_ids) - 1:
                    output.finish_reason = FinishReason.LENGTH
                    self.request_finished[req_idx] = True
                if new_token_id == self.eos_token_id:
                    output.finish_reason = FinishReason.STOP
                    self.request_finished[req_idx] = True
                if new_token_id in (self.stop_token_ids or ()):
                    output.finish_reason = FinishReason.STOP
                    output.stop_reason = new_token_id
                    self.request_finished[req_idx] = True
                outputs.append(output)

                self.request_token_idx[req_idx] += 1

        return outputs