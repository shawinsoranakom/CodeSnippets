async def run_loop() -> bool:
            """Run the agent loop. Returns True if finished normally."""
            nonlocal cumulative_cost

            for step_num in range(self.config.max_steps):
                # Propose next action
                proposal = await agent.propose_action()

                # Get cumulative cost from LLM provider
                if self._llm_provider:
                    cumulative_cost = self._llm_provider.get_incurred_cost()

                # Check for finish command - record it and return
                if proposal.use_tool.name == "finish":
                    steps.append(
                        StepResult(
                            step_num=step_num + 1,
                            tool_name=proposal.use_tool.name,
                            tool_args=proposal.use_tool.arguments,
                            result="Agent finished",
                            is_error=False,
                            cumulative_cost=cumulative_cost,
                        )
                    )
                    return True

                # Execute the action
                result = await agent.execute(proposal)

                # Update cost after execution
                if self._llm_provider:
                    cumulative_cost = self._llm_provider.get_incurred_cost()

                # Get result info
                result_str = str(getattr(result, "outputs", result))
                is_error = hasattr(result, "status") and result.status == "error"

                # Record step
                steps.append(
                    StepResult(
                        step_num=step_num + 1,
                        tool_name=proposal.use_tool.name,
                        tool_args=proposal.use_tool.arguments,
                        result=result_str,
                        is_error=is_error,
                        cumulative_cost=cumulative_cost,
                    )
                )

                # Call step callback if provided
                if self.step_callback:
                    # Truncate result for display
                    result_preview = (
                        result_str[:100] + "..."
                        if len(result_str) > 100
                        else result_str
                    )
                    result_preview = result_preview.replace("\n", " ")
                    self.step_callback(
                        self.config.config_name,
                        challenge.name,
                        step_num + 1,
                        proposal.use_tool.name,
                        result_preview,
                        is_error,
                    )

            return False