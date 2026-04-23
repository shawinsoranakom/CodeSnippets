def parse_response_content(
        self,
        response: AssistantChatMessage,
    ) -> ReflexionActionProposal:
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

        assistant_reply_dict = extract_dict_from_json(response.content)
        self.logger.debug(
            "Parsing object extracted from LLM response:\n"
            f"{json.dumps(assistant_reply_dict, indent=4)}"
        )

        if not response.tool_calls:
            raise InvalidAgentResponseError("Assistant did not use a tool")

        assistant_reply_dict["use_tool"] = response.tool_calls[0].function

        # If we're in reflection phase, process the reflection
        if self.current_phase == ReflexionPhase.REFLECTING:
            # Check if this is a verbal reflection
            reflection_format = self._get_reflection_format()
            if reflection_format == "verbal":
                # Extract verbal reflection text from response
                # It starts after "Reflection: " prefix
                verbal_text = response.content
                if verbal_text.startswith("Reflection:"):
                    verbal_text = verbal_text[len("Reflection:") :].strip()
                self._process_reflection(assistant_reply_dict, verbal_text=verbal_text)
            else:
                self._process_reflection(assistant_reply_dict)
            # After reflection, move back to proposing
            self.current_phase = ReflexionPhase.PROPOSING

        # Phase and reflection_context are stored in strategy state, not in the proposal

        # Ensure thoughts has all required fields for ReflexionThoughts model
        thoughts = assistant_reply_dict.get("thoughts", {})
        if not isinstance(thoughts, dict):
            thoughts = {}
        # Set defaults for all required fields
        if "observations" not in thoughts:
            thoughts["observations"] = thoughts.get("text", "")
        if "reasoning" not in thoughts:
            thoughts["reasoning"] = ""
        if "self_reflection" not in thoughts:
            thoughts["self_reflection"] = thoughts.get("reasoning", "")
        if "self_criticism" not in thoughts:
            thoughts["self_criticism"] = thoughts.get("criticism", "")
        if "plan" not in thoughts:
            thoughts["plan"] = thoughts.get("plan", [])
            if isinstance(thoughts["plan"], str):
                thoughts["plan"] = [thoughts["plan"]] if thoughts["plan"] else []
        if "lessons_applied" not in thoughts:
            thoughts["lessons_applied"] = []
        assistant_reply_dict["thoughts"] = thoughts

        parsed_response = ReflexionActionProposal.model_validate(assistant_reply_dict)
        parsed_response.raw_message = response.model_copy()

        # Record the action for later reflection (when in proposing phase)
        # This ensures we track what action was taken so we can reflect on it
        # after seeing the result in the next build_prompt() call
        if self.current_phase == ReflexionPhase.PROPOSING and parsed_response.use_tool:
            self.record_action(
                action_name=parsed_response.use_tool.name,
                action_arguments=parsed_response.use_tool.arguments,
            )
            self.logger.debug(
                f"Reflexion: Recorded action {parsed_response.use_tool.name} "
                "for reflection"
            )

        return parsed_response