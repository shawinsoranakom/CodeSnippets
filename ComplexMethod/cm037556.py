def extract_reasoning_streaming(
        self,
        previous_text: str,
        current_text: str,
        delta_text: str,
        previous_token_ids: Sequence[int],
        current_token_ids: Sequence[int],
        delta_token_ids: Sequence[int],
    ) -> DeltaMessage | None:
        """Extract content using token ID sequence state machine"""
        # Define sequences
        think_start_sequence = self.think_start_ids
        response_start_sequence = self.response_start_ids
        response_end_sequence = self.response_end_ids

        assert len(delta_token_ids) == 1
        # Process each token in the delta
        token = delta_token_ids[0]

        def check_token_with_sequence(token):
            if self.current_state == "idle" or self.current_state == "think":
                return (
                    token == self.expected_sequence[self.sequence_index]
                    or token == self.expected_sequence_side[self.sequence_index]
                )
            else:
                return token == self.expected_sequence[self.sequence_index]

        def check_last_token(token):
            if self.current_state == "idle" or self.current_state == "think":
                # only return true if it's judge using a side sequence.
                if (
                    self.sequence_index - 1 < len(self.expected_sequence_side)
                    and token == self.expected_sequence_side[self.sequence_index - 1]
                ):
                    return self.sequence_index == len(self.expected_sequence_side)
                else:
                    return self.sequence_index == len(self.expected_sequence)
            else:
                return self.sequence_index == len(self.expected_sequence)

        # Check if token matches expected sequence
        token_in_state_seq = check_token_with_sequence(token)

        if token_in_state_seq:
            # Store matching token
            self.token_buffer.append(token)
            self.text_buffer += delta_text
            self.sequence_index += 1
            ## state change from idle->think->response->idle

            # Check if sequence fully matched
            if check_last_token(token):
                # State transition
                if self.current_state == "idle":
                    self.current_state = "think"
                    self.expected_sequence = response_start_sequence
                    self.expected_sequence_side = self.response_start_ids_fast
                elif self.current_state == "think":
                    self.current_state = "response"
                    self.expected_sequence = response_end_sequence
                elif self.current_state == "response":
                    self.current_state = "idle"
                    self.expected_sequence = think_start_sequence
                    self.expected_sequence_side = self.think_start_ids_fast

                # Reset matching state
                self.sequence_index = 0
                self.token_buffer = []
                self.text_buffer = ""
                # Do not send content for state transition texts.
        else:
            # Sequence broken - handle buffered content
            if self.token_buffer and len(self.token_buffer) > 0:
                # Send buffered tokens
                buffered_content = self.text_buffer + delta_text
                # Reset matching state
                self.sequence_index = 0
                self.token_buffer = []
                self.text_buffer = ""

                # Return content based on current state
                if self.current_state == "think":
                    return DeltaMessage(reasoning=buffered_content, content=None)
                else:
                    return DeltaMessage(reasoning=None, content=buffered_content)
            else:
                # No buffered content, send normally
                if self.current_state == "think":
                    return DeltaMessage(reasoning=delta_text, content=None)
                else:
                    return DeltaMessage(reasoning=None, content=delta_text)

        # If no content to send in this delta
        return None