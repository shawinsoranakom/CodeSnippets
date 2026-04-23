async def _create_initial_plan(self, request: str) -> None:
        """Create an initial plan based on the request using the flow's LLM and PlanningTool."""
        logger.info(f"Creating initial plan with ID: {self.active_plan_id}")

        system_message_content = (
            "You are a planning assistant. Create a concise, actionable plan with clear steps. "
            "Focus on key milestones rather than detailed sub-steps. "
            "Optimize for clarity and efficiency."
        )
        agents_description = []
        for key in self.executor_keys:
            if key in self.agents:
                agents_description.append(
                    {
                        "name": key.upper(),
                        "description": self.agents[key].description,
                    }
                )
        if len(agents_description) > 1:
            # Add description of agents to select
            system_message_content += (
                f"\nNow we have {agents_description} agents. "
                f"The infomation of them are below: {json.dumps(agents_description)}\n"
                "When creating steps in the planning tool, please specify the agent names using the format '[agent_name]'."
            )

        # Create a system message for plan creation
        system_message = Message.system_message(system_message_content)

        # Create a user message with the request
        user_message = Message.user_message(
            f"Create a reasonable plan with clear steps to accomplish the task: {request}"
        )

        # Call LLM with PlanningTool
        response = await self.llm.ask_tool(
            messages=[user_message],
            system_msgs=[system_message],
            tools=[self.planning_tool.to_param()],
            tool_choice=ToolChoice.AUTO,
        )

        # Process tool calls if present
        if response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call.function.name == "planning":
                    # Parse the arguments
                    args = tool_call.function.arguments
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse tool arguments: {args}")
                            continue

                    # Ensure plan_id is set correctly and execute the tool
                    args["plan_id"] = self.active_plan_id

                    # Execute the tool via ToolCollection instead of directly
                    result = await self.planning_tool.execute(**args)

                    logger.info(f"Plan creation result: {str(result)}")
                    return

        # If execution reached here, create a default plan
        logger.warning("Creating default plan")

        # Create default plan using the ToolCollection
        await self.planning_tool.execute(
            **{
                "command": "create",
                "plan_id": self.active_plan_id,
                "title": f"Plan for: {request[:50]}{'...' if len(request) > 50 else ''}",
                "steps": ["Analyze request", "Execute task", "Verify results"],
            }
        )