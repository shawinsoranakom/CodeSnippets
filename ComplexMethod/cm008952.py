async def test_async_mixed_emulated_and_real_tools(self) -> None:
        """Test that some tools can be emulated while others execute normally in async mode."""
        agent_model = FakeModel(
            messages=cycle(
                [
                    AIMessage(
                        content="",
                        tool_calls=[
                            {"name": "get_weather", "id": "1", "args": {"location": "NYC"}},
                            {"name": "calculator", "id": "2", "args": {"expression": "10*2"}},
                        ],
                    ),
                    AIMessage(content="Both completed."),
                ]
            )
        )

        emulator_model = FakeEmulatorModel(responses=["Emulated: 65°F in NYC"])

        # Only emulate get_weather
        emulator = LLMToolEmulator(tools=["get_weather"], model=emulator_model)

        agent = create_agent(
            model=agent_model,
            tools=[get_weather, calculator],
            middleware=[emulator],
        )

        result = await agent.ainvoke({"messages": [HumanMessage("Weather and calculate")]})

        tool_messages = [msg for msg in result["messages"] if hasattr(msg, "name")]
        assert len(tool_messages) >= 2

        # Calculator should have real result
        calc_messages = [msg for msg in tool_messages if msg.name == "calculator"]
        assert len(calc_messages) > 0
        assert "Result: 20" in calc_messages[0].content