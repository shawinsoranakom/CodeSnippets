def append_output(self, output) -> None:
        self.last_output = output
        if not isinstance(output, RequestOutput):
            raise ValueError("SimpleContext only supports RequestOutput.")
        self.num_prompt_tokens = len(output.prompt_token_ids or [])
        self.num_cached_tokens = output.num_cached_tokens or 0
        self.num_output_tokens += len(output.outputs[0].token_ids or [])
        if output.kv_transfer_params is not None:
            self.kv_transfer_params = output.kv_transfer_params

        # Accumulate text, token_ids, and logprobs for streaming mode
        delta_output = output.outputs[0]
        self._accumulated_text += delta_output.text
        self._accumulated_token_ids.extend(delta_output.token_ids)
        if delta_output.logprobs is not None:
            self._accumulated_logprobs.extend(delta_output.logprobs)

        if len(self.input_messages) == 0:
            output_prompt = output.prompt or ""
            output_prompt_token_ids = output.prompt_token_ids or []
            self.input_messages.append(
                ResponseRawMessageAndToken(
                    message=output_prompt,
                    tokens=output_prompt_token_ids,
                )
            )