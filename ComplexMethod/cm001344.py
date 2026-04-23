def parse_response_content(
        self,
        response: AssistantChatMessage,
    ) -> PlanExecuteActionProposal:
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

        # Handle variable extraction phase (PS+)
        if self.current_phase == PlanExecutePhase.VARIABLE_EXTRACTION:
            self._process_variable_extraction(response.content)
            # After extraction, move to planning phase
            self.current_phase = PlanExecutePhase.PLANNING
        # Extract plan from response if in planning phase
        elif self.current_phase == PlanExecutePhase.PLANNING:
            plan = self._extract_plan_from_response(response.content)
            if plan:
                self.current_plan = plan
                self.current_phase = PlanExecutePhase.EXECUTING
                # Mark that we need to advance after this action executes
                self._pending_step_advance = False
        elif self.current_phase == PlanExecutePhase.REPLANNING:
            plan = self._extract_plan_from_response(response.content)
            if plan:
                # Preserve completed steps from old plan
                if self.current_plan:
                    plan.completed_steps = self.current_plan.completed_steps
                self.current_plan = plan
                self.current_phase = PlanExecutePhase.EXECUTING
                self.replan_count += 1
                self._pending_step_advance = False
        elif self.current_phase == PlanExecutePhase.EXECUTING and self.current_plan:
            # If we have a pending advance from the previous action, do it now
            if getattr(self, "_pending_step_advance", False):
                current_step = self.current_plan.get_current_step()
                if current_step:
                    self.current_plan.advance_step("Executed")
            # Mark that the current action needs to be advanced after execution
            self._pending_step_advance = True

        # Plan and phase are stored in strategy state, not in the proposal
        parsed_response = PlanExecuteActionProposal.model_validate(assistant_reply_dict)
        parsed_response.raw_message = response.model_copy()

        return parsed_response