def parse_response_content(
        self,
        response: AssistantChatMessage,
    ) -> ToTActionProposal:
        """Parse the LLM response."""
        if not response.content:
            raise InvalidAgentResponseError("Assistant response has no text content")

        self.logger.debug(
            "LLM response content:"
            + (
                f"\n{response.content}"
                if "\n" in response.content
                else f" '{response.content}'"
            )
        )

        # Handle different phases
        if self.current_phase == ToTPhase.GENERATING:
            self._process_generation(response.content)
            self.current_phase = ToTPhase.EVALUATING
        elif self.current_phase == ToTPhase.EVALUATING:
            self._process_evaluation(response.content)
            self.current_phase = ToTPhase.SELECTING

        # Parse the final response
        assistant_reply_dict = extract_dict_from_json(response.content)
        self.logger.debug(
            "Parsing object extracted from LLM response:\n"
            f"{json.dumps(assistant_reply_dict, indent=4)}"
        )

        if not response.tool_calls:
            # If no tool call but we found a good path, use that action
            if self.tree:
                best_action = self.tree.get_best_terminal_action()
                if best_action:
                    assistant_reply_dict["use_tool"] = best_action.model_dump()
                else:
                    raise InvalidAgentResponseError("Assistant did not use a tool")
            else:
                raise InvalidAgentResponseError("Assistant did not use a tool")
        else:
            assistant_reply_dict["use_tool"] = response.tool_calls[0].function

        # Note: thought_path, alternatives_explored, and phase are stored in
        # strategy state, not in the proposal

        parsed_response = ToTActionProposal.model_validate(assistant_reply_dict)
        parsed_response.raw_message = response.model_copy()

        # Move to next iteration
        self.iteration_count += 1
        self.current_phase = ToTPhase.GENERATING

        return parsed_response