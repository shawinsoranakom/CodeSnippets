def append_output(self, output: RequestOutput) -> None:
        self.num_prompt_tokens = len(output.prompt_token_ids or [])
        self.num_cached_tokens = output.num_cached_tokens or 0
        self.num_output_tokens += len(output.outputs[0].token_ids or [])
        if output.kv_transfer_params is not None:
            self.kv_transfer_params = output.kv_transfer_params
        self.parser.process(output.outputs[0])
        output_token_ids = output.outputs[0].token_ids or []
        self._accumulated_token_ids.extend(output_token_ids)

        # only store if enable_response_messages is True, save memory
        if self.request.enable_response_messages:
            output_prompt = output.prompt or ""
            output_prompt_token_ids = output.prompt_token_ids or []
            if len(self.input_messages) == 0:
                self.input_messages.append(
                    ResponseRawMessageAndToken(
                        message=output_prompt,
                        tokens=output_prompt_token_ids,
                    )
                )
            else:
                self.output_messages.append(
                    ResponseRawMessageAndToken(
                        message=output_prompt,
                        tokens=output_prompt_token_ids,
                    )
                )
            self.output_messages.append(
                ResponseRawMessageAndToken(
                    message=output.outputs[0].text,
                    tokens=output.outputs[0].token_ids,
                )
            )