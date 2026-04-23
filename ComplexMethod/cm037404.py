def condense(self, empty_req_indices: list[int]) -> None:
        """Move non-empty requests down into lower, empty indices.

        Args:
          empty_req_indices: empty batch indices, sorted descending.
        """
        num_reqs = self.num_reqs
        if num_reqs == 0:
            # The batched states are empty.
            self._req_ids.clear()
            self.req_output_token_ids.clear()
            return

        # NOTE(woosuk): This function assumes that the empty_req_indices
        # is sorted in descending order.
        last_req_index = num_reqs + len(empty_req_indices) - 1
        while empty_req_indices:
            # Find the largest non-empty index.
            while last_req_index in empty_req_indices:
                last_req_index -= 1

            # Find the smallest empty index.
            empty_index = empty_req_indices.pop()
            if empty_index >= last_req_index:
                break

            # Swap the states.
            req_id = self._req_ids[last_req_index]
            output_token_ids = self.req_output_token_ids[last_req_index]
            assert req_id is not None
            self._req_ids[empty_index] = req_id
            self._req_ids[last_req_index] = None
            self.req_output_token_ids[empty_index] = output_token_ids
            self.req_output_token_ids[last_req_index] = None
            self.req_id_to_index[req_id] = empty_index

            num_tokens = self.num_tokens_no_spec[last_req_index]
            self.token_ids_cpu[empty_index, :num_tokens] = self.token_ids_cpu[
                last_req_index, :num_tokens
            ]
            self.num_tokens_no_spec[empty_index] = self.num_tokens_no_spec[
                last_req_index
            ]
            self.num_prompt_tokens[empty_index] = self.num_prompt_tokens[last_req_index]
            self.num_computed_tokens_cpu[empty_index] = self.num_computed_tokens_cpu[
                last_req_index
            ]
            self.block_table.move_row(last_req_index, empty_index)
            self.temperature_cpu[empty_index] = self.temperature_cpu[last_req_index]
            self.top_p_cpu[empty_index] = self.top_p_cpu[last_req_index]
            self.top_k_cpu[empty_index] = self.top_k_cpu[last_req_index]
            self.frequency_penalties_cpu[empty_index] = self.frequency_penalties_cpu[
                last_req_index
            ]
            self.presence_penalties_cpu[empty_index] = self.presence_penalties_cpu[
                last_req_index
            ]
            self.repetition_penalties_cpu[empty_index] = self.repetition_penalties_cpu[
                last_req_index
            ]
            self.min_p_cpu[empty_index] = self.min_p_cpu[last_req_index]
            generator = self.generators.pop(last_req_index, None)
            if generator is not None:
                self.generators[empty_index] = generator

            min_token = self.min_tokens.pop(last_req_index, None)
            if min_token is not None:
                self.min_tokens[empty_index] = min_token

            self.request_lora_mapping[empty_index] = self.request_lora_mapping[
                last_req_index
            ]

            self.logit_bias[empty_index] = self.logit_bias[last_req_index]

            if self.allowed_token_ids_mask_cpu_tensor is not None:
                self.allowed_token_ids_mask_cpu_tensor[empty_index] = (
                    self.allowed_token_ids_mask_cpu_tensor[last_req_index]
                )

            bad_words_token_ids = self.bad_words_token_ids.pop(last_req_index, None)
            if bad_words_token_ids is not None:
                self.bad_words_token_ids[empty_index] = bad_words_token_ids
            # Decrement last_req_index since it is now empty.
            last_req_index -= 1

        # Trim lists to the batch size.
        del self._req_ids[self.num_reqs :]
        del self.req_output_token_ids[self.num_reqs :]