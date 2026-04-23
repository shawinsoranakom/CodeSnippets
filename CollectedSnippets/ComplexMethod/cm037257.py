def _update_think_state(self, state: dict[str, Any]):
        """Updates the state based on newly generated output tokens."""
        if not state.get("in_end", False) and state.get("check_count_down", 0) > 0:
            state["check_count_down"] -= 1
            return

        output = state.get("output_tok_ids", [])
        if not output:
            return

        # Track previous output length for incremental processing
        prev_length = state.get("prev_output_length", 0)
        current_length = len(output)

        if current_length <= prev_length:
            return

        # Process only newly added tokens
        new_tokens = output[prev_length:]
        state["prev_output_length"] = current_length

        # Check if new tokens contain think start or end sequences
        start_len = len(self.reasoning_start_token_ids)
        end_len = len(self.reasoning_end_token_ids)

        # Look for think sequences in recent tokens (including boundary)
        # Check overlapping regions where sequences might span boundaries
        check_start_idx = max(0, prev_length - max(start_len, end_len) + 1)
        recent_tokens = output[check_start_idx:]

        # Find any think start/end sequences in recent tokens
        recent_start_pos = self._find_last_sequence_index(
            recent_tokens, self.reasoning_start_token_ids
        )
        recent_end_pos = self._find_last_sequence_index(
            recent_tokens, self.reasoning_end_token_ids
        )

        # Update state based on recent sequences
        if not state["in_end"]:
            if recent_start_pos >= 0 and recent_end_pos >= 0:
                if recent_start_pos > recent_end_pos:
                    # Case: ...<end>...<start>... - entering think mode
                    absolute_start_pos = check_start_idx + recent_start_pos
                    new_think_count = current_length - (absolute_start_pos + start_len)
                    state["in_think"] = True
                    state["think_count"] = new_think_count
                else:
                    # Case: ...<start>...<end>... - exiting think mode
                    state["in_think"] = False
                    state["think_count"] = 0
            elif recent_start_pos >= 0:
                # Found think start - entering think mode
                absolute_start_pos = check_start_idx + recent_start_pos
                new_think_count = current_length - (absolute_start_pos + start_len)
                state["in_think"] = True
                state["think_count"] = new_think_count
            elif recent_end_pos >= 0:
                # Found think end - exiting think mode
                state["in_think"] = False
                state["think_count"] = 0
            elif state["in_think"]:
                # Continue thinking mode, increment count by new tokens
                state["think_count"] += len(new_tokens)

            # Set countdown based on current state
            if state["in_think"]:
                remaining_budget = max(
                    0, state["thinking_token_budget"] - state["think_count"]
                )
                state["check_count_down"] = max(0, remaining_budget - 1)
            else:
                state["check_count_down"] = state["thinking_token_budget"]

            # Check if need to transition to end mode
            if (
                state["in_think"]
                and state["think_count"] >= state["thinking_token_budget"]
            ):
                state["in_think"] = False
                state["in_end"] = True
                state["end_count"] = 0
                state["check_count_down"] = state["thinking_token_budget"]
        else:
            # In end mode
            state["end_count"] += 1
            if state["end_count"] >= len(self.reasoning_end_token_ids):
                state.update(
                    {
                        "in_end": False,
                        "end_count": 0,
                        "check_count_down": state["thinking_token_budget"],
                    }
                )