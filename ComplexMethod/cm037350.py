def update_async_spec_token_ids(self, draft_token_ids: list[list[int]]) -> None:
        """
        In async scheduling case, update spec_token_ids in sampling metadata with
        real draft token ids from prior step. This is called right before they are
        needed by the rejection sampler for penalty/bad_words computation.
        """
        if not draft_token_ids or not self.prev_req_id_to_index:
            return

        if (spec_token_ids := self.sampling_metadata.spec_token_ids) is not None:
            for req_id, spec_ids in zip(self.req_ids, spec_token_ids):
                if spec_ids:
                    prev_index = self.prev_req_id_to_index.get(req_id)
                    if prev_index is not None:
                        draft_ids = draft_token_ids[prev_index]
                        if draft_ids:
                            del draft_ids[len(spec_ids) :]
                            spec_ids.clear()
                            spec_ids.extend(draft_ids)