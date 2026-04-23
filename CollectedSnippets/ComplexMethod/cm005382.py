def put(self, value: "torch.Tensor") -> None:
        """Called by ``model.generate()`` after each decode step with new token(s)."""
        if self._cancelled.is_set():
            raise _GenerationCancelled()
        # The first put() contains the prompt tokens — skip since we only stream generated tokens.
        if self._first:
            self._first = False
            return
        for token_id in value.tolist():
            self.total_tokens += 1
            self.generated_token_ids.append(token_id)

            if token_id == self._stc_id:
                self._inside_tool_call = True
            elif token_id == self._etc_id:
                self._inside_tool_call = False

            text = self._decode_stream.step(self._tokenizer, token_id)
            if text is not None and not self._inside_tool_call and token_id != self._etc_id:
                self._loop.call_soon_threadsafe(self._queue.put_nowait, text)