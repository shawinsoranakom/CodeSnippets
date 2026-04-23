def update_state(self, batch_update: BatchUpdate | None):
        if not self.is_enabled:
            return
        if batch_update:
            for index, params, prompt_tok_ids, output_tok_ids in batch_update.added:
                thinking_token_budget = params.thinking_token_budget

                if thinking_token_budget is not None:
                    self._state[index] = self._init_state_entry(
                        prompt_tok_ids, thinking_token_budget
                    )
                    self._state[index]["output_tok_ids"] = output_tok_ids
                else:
                    # Remove state if no thinking budget
                    self._state.pop(index, None)

            for index in batch_update.removed:
                self._state.pop(index, {})

            for i1, i2, direction in batch_update.moved:
                if direction == MoveDirectionality.SWAP:
                    state1 = self._state.pop(i1, None)
                    state2 = self._state.pop(i2, None)
                    if state1 is not None:
                        self._state[i2] = state1
                    if state2 is not None:
                        self._state[i1] = state2
                else:
                    state = self._state.pop(i1, None)
                    if state is not None:
                        self._state[i2] = state

        for state in self._state.values():
            self._update_think_state(state)