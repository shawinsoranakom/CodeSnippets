def _prepare_assistant_input_ids(self, input_ids: torch.LongTensor) -> tuple[torch.LongTensor, int]:
        """Converts target input IDs to assistant input IDs, handling discrepancies."""
        convert_kwargs = {
            "source_tokenizer": self.target_tokenizer,
            "destination_tokenizer": self.assistant_tokenizer,
        }
        remove_from_pkv = 0

        if self.prev_assistant_ids is not None and self.prev_target_ids_len > self.target_lookbehind:
            # input_ids contains all target prompt input ids and some new target input ids
            start_index_in_target_window = self.prev_target_ids_len - self.target_lookbehind

            new_assistant_ids = self.convert_source_tokens_to_target_tokens(
                input_ids[:, start_index_in_target_window:], **convert_kwargs
            )
            prompt_use_length = new_assistant_ids.shape[1]
            prompt_use = self.prev_assistant_ids[:, -prompt_use_length:]

            discrepancy_length, new_tokens_only, discrepancy_only = self._get_tokens_diag(
                prompt_use, new_assistant_ids
            )
            assistant_input_ids = self.prev_assistant_ids

            if new_tokens_only is not None:
                if discrepancy_length > 0 and discrepancy_only.shape[1] > 0:
                    if discrepancy_length == discrepancy_only.shape[1]:
                        assistant_input_ids[:, -discrepancy_length:] = discrepancy_only

                    elif discrepancy_length > discrepancy_only.shape[1]:
                        discrepancy_length_diff = discrepancy_length - discrepancy_only.shape[1]
                        assistant_input_ids = assistant_input_ids[:, :-discrepancy_length_diff]
                        assistant_input_ids[:, -discrepancy_only.shape[1] :] = discrepancy_only

                    remove_from_pkv = discrepancy_length

                if new_tokens_only.shape[1] > 0:
                    assistant_input_ids = torch.cat([assistant_input_ids, new_tokens_only], dim=-1)
            else:
                # edge case: in case of no intersection between prompt and new_assistant_ids
                assistant_input_ids = torch.cat([assistant_input_ids, new_assistant_ids], dim=-1)
        else:
            assistant_input_ids = self.convert_source_tokens_to_target_tokens(input_ids, **convert_kwargs)
            self.prev_target_ids_len = input_ids.shape[1]

        return assistant_input_ids, remove_from_pkv