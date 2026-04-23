def apply_streaming_update(self, update: StreamingUpdate) -> None:
        # Apply the update to the request state.
        self.streaming_input = not update.final
        # TODO also include relevant output tokens in new prompt here
        #     (match scheduler behavior).
        if update.prompt:
            self.prompt = (
                (self.prompt + update.prompt) if self.prompt else update.prompt
            )
        if self.prompt_token_ids:
            self.prompt_token_ids.extend(update.prompt_token_ids or ())
        else:
            self.prompt_token_ids = update.prompt_token_ids or []
        assert self.prompt_token_ids is not None
        self.prompt_len = len(self.prompt_token_ids)
        if self.stats is not None:
            self.stats.arrival_time = update.arrival_time
        self.is_prefilling = True