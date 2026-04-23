def parse_response_content(
        self,
        response: AssistantChatMessage,
    ) -> ReWOOActionProposal:
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

        # Parse plan from response FIRST if in planning phase.
        # During PLANNING, we expect plan text format, not JSON
        if self.current_phase == ReWOOPhase.PLANNING:
            self.logger.info("ReWOO: Attempting to extract plan from PLANNING response")
            plan = self._extract_plan_from_response(response.content)
            if plan and plan.steps:
                self.current_plan = plan
                # Transition to EXECUTING phase now that we have a plan
                self.current_phase = ReWOOPhase.EXECUTING
                self.logger.info(
                    f"ReWOO: Extracted plan with {len(plan.steps)} steps, "
                    f"transitioning to EXECUTING phase"
                )

                # Use the first step of the plan as the action to execute
                first_step = plan.steps[0]
                first_action = AssistantFunctionCall(
                    name=first_step.tool_name,
                    arguments=first_step.tool_arguments,
                )

                # Build a complete proposal from the plan
                thoughts = ReWOOThoughts(
                    observations="Created ReWOO execution plan",
                    reasoning=first_step.thought,
                    plan=[f"{s.variable_name}: {s.thought}" for s in plan.steps],
                )

                # Create synthetic raw message
                from forge.llm.providers.schema import AssistantToolCall

                raw_message = AssistantChatMessage(
                    content=response.content,
                    tool_calls=[
                        AssistantToolCall(
                            id="rewoo_plan_step_0",
                            type="function",
                            function=first_action,
                        )
                    ],
                )

                return ReWOOActionProposal(
                    thoughts=thoughts,
                    use_tool=first_action,
                    raw_message=raw_message,
                )
            else:
                self.logger.warning(
                    "ReWOO: Failed to extract plan from response, staying in PLANNING. "
                    f"Plan: {plan}, Steps: {plan.steps if plan else 'N/A'}"
                )
                # Fall through to standard JSON parsing if plan extraction fails

        # For non-planning phases or if plan extraction failed, parse as JSON
        assistant_reply_dict = extract_dict_from_json(response.content)
        self.logger.debug(
            "Parsing object extracted from LLM response:\n"
            f"{json.dumps(assistant_reply_dict, indent=4)}"
        )

        if not response.tool_calls:
            raise InvalidAgentResponseError("Assistant did not use a tool")

        assistant_reply_dict["use_tool"] = response.tool_calls[0].function

        # Ensure thoughts dict has required fields
        thoughts_dict = assistant_reply_dict.get("thoughts", {})
        if not isinstance(thoughts_dict, dict):
            thoughts_dict = {"observations": "", "reasoning": ""}
        if "observations" not in thoughts_dict:
            thoughts_dict["observations"] = ""
        if "reasoning" not in thoughts_dict:
            thoughts_dict["reasoning"] = ""
        assistant_reply_dict["thoughts"] = thoughts_dict

        parsed_response = ReWOOActionProposal.model_validate(assistant_reply_dict)
        parsed_response.raw_message = response.model_copy()

        return parsed_response