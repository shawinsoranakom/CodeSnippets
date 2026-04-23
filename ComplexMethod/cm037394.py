def correct_spec_decode_token_counts():
                valid_sampled_token_count = self._get_valid_sampled_token_count()
                if not valid_sampled_token_count:
                    return
                prev_req_id_to_index = self.input_batch.prev_req_id_to_index
                if not prev_req_id_to_index:
                    return
                for (
                    req_id,
                    optimistic_num_accepted,
                    req_state,
                ) in deferred_spec_decode_corrections:
                    prev_req_index = prev_req_id_to_index.get(req_id)
                    if prev_req_index is None:
                        continue
                    num_accepted = valid_sampled_token_count[prev_req_index] - 1
                    correction = optimistic_num_accepted - num_accepted
                    req_state.num_computed_tokens -= correction
                    cur_req_index = self.input_batch.req_id_to_index.get(req_id)
                    if cur_req_index is None:
                        continue
                    self.input_batch.num_computed_tokens_cpu[cur_req_index] -= (
                        correction
                    )
                    if is_ngram_gpu and correction > 0:
                        self.input_batch.num_tokens_no_spec[cur_req_index] -= correction
                        self.num_tokens_no_spec_gpu[cur_req_index] -= correction