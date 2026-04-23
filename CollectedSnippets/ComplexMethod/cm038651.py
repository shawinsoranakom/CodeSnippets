def append_output(self, output: RequestOutput) -> None:
        # append_output is called for each output token in streaming case,
        # so we only want to add the prompt tokens once for each message.
        self.last_content_delta = None
        if self.first_tok_of_message:
            self._update_prefill_token_usage(output)
        # Reset self.first_tok_of_message if needed:
        # if the current token is the last one of the current message
        # (finished=True), then the next token processed will mark the
        # beginning of a new message
        self.first_tok_of_message = output.finished
        last_delta_text = ""
        for tok in output.outputs[0].token_ids:
            self.parser.process(tok)
            last_delta_text += self.parser.last_content_delta or ""
        if last_delta_text:
            self.last_content_delta = last_delta_text
        self._update_decode_token_usage(output)
        if output.kv_transfer_params is not None:
            self.kv_transfer_params = output.kv_transfer_params

        # For streaming, update previous turn when message is complete
        if output.finished:
            self.all_turn_metrics.append(self.current_turn_metrics.copy())
            self.current_turn_metrics.reset()
        # Check if the current token is part of reasoning content
        self._update_num_reasoning_tokens()
        self.last_tok = tok
        if len(self._messages) - self.num_init_messages < len(self.parser.messages):
            self._messages.extend(
                self.parser.messages[len(self._messages) - self.num_init_messages :]
            )