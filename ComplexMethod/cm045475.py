async def test_agent(
        component: ComponentModel, model_client: Optional[ChatCompletionClient] = None
    ) -> ComponentTestResult:
        """Test an agent component with a simple message"""
        try:
            from autogen_agentchat.agents import AssistantAgent
            from autogen_agentchat.messages import TextMessage
            from autogen_core import CancellationToken

            # Try to load the agent
            try:
                # Construct the agent with the model client if provided
                if model_client:
                    component.config["model_client"] = model_client

                agent = AssistantAgent.load_component(component)

                logs = ["Agent component loaded successfully"]
            except Exception as e:
                return ComponentTestResult(
                    status=False,
                    message=f"Failed to initialize agent: {str(e)}",
                    logs=[f"Agent initialization error: {str(e)}"],
                )

            # Test the agent with a simple message
            test_question = "What is 2+2? Keep it brief."
            try:
                response = await agent.on_messages(
                    [TextMessage(content=test_question, source="user")],
                    cancellation_token=CancellationToken(),
                )

                # Check if we got a valid response
                status = response and response.chat_message is not None

                if status:
                    logs.append(
                        f"Agent responded with: {response.chat_message.to_text()} to the question : {test_question}"
                    )
                else:
                    logs.append("Agent did not return a valid response")

                return ComponentTestResult(
                    status=status,
                    message="Agent test completed successfully" if status else "Agent test failed - no valid response",
                    data=response.chat_message.model_dump() if status else None,
                    logs=logs,
                )
            except Exception as e:
                return ComponentTestResult(
                    status=False,
                    message=f"Error during agent response: {str(e)}",
                    logs=logs + [f"Agent response error: {str(e)}"],
                )

        except Exception as e:
            return ComponentTestResult(
                status=False, message=f"Error testing agent component: {str(e)}", logs=[f"Exception: {str(e)}"]
            )