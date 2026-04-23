def update_async_output_token_ids(self) -> None:
        """
        In async scheduling case, update output_token_ids in sampling metadata
        from prior steps sampled token ids once they've finished copying to CPU.
        This is called right before they are needed by the logits processors.
        """
        output_token_ids = self.sampling_metadata.output_token_ids
        if self.sampled_token_ids_cpu is None or not output_token_ids:
            # Output token ids not needed or not async scheduling.
            return

        assert self.prev_req_id_to_index is not None
        sampled_token_ids = None
        for index, req_id in enumerate(self.req_ids):
            prev_index = self.prev_req_id_to_index.get(req_id)
            if prev_index is None:
                continue
            req_output_token_ids = output_token_ids[index]
            if not req_output_token_ids or req_output_token_ids[-1] != -1:
                # Final output id is not a placeholder, some tokens must have
                # been discarded after a kv-load failure.
                continue
            if sampled_token_ids is None:
                assert self.async_copy_ready_event is not None
                self.async_copy_ready_event.synchronize()
                sampled_token_ids = self.sampled_token_ids_cpu.tolist()
            # Replace placeholder token id(s) with actual sampled id(s).
            new_ids: list[int] = sampled_token_ids[prev_index]
            if not new_ids:
                continue
            num_sampled_ids = len(new_ids) if new_ids[-1] != -1 else new_ids.index(-1)
            # Also account for case where there may be a smaller number of
            # output placeholders (tokens can be discarded after kv-load
            # failure) or a larger number (async spec decode adds optimistic
            # placeholders that may exceed the actual acceptance count).
            first_placeholder = req_output_token_ids.index(-1)
            num_placeholders = len(req_output_token_ids) - first_placeholder
            num_to_replace = min(num_sampled_ids, num_placeholders)
            del new_ids[num_to_replace:]
            req_output_token_ids[first_placeholder:] = new_ids