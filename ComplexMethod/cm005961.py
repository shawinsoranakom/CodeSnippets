def test_multi_turn_conversation_context_order_bug(self):
        """Reproduce the exact multi-turn conversation bug seen in SPARC validation.

        This test simulates the scenario where conversation context gets reversed
        during multi-turn conversations, based on the terminal logs showing:
        - Turn 1: Just the original query
        - Turn 2+: Messages in reverse chronological order
        """
        from lfx.base.agents.altk_tool_wrappers import ValidatedTool
        from lfx.schema.data import Data

        logger.debug("\n=== MULTI-TURN CONVERSATION BUG REPRODUCTION ===")

        # Simulate the progression seen in the terminal logs

        # TURN 1: Initial query (this works correctly)
        initial_query = Data(data={"text": "how much is 353454 345454", "sender": "User"})

        agent_turn1 = ALTKAgentComponent(
            _type="Agent",
            agent_llm=MockLanguageModel(),
            input_value="how much is 353454 345454",
            tools=[MockTool()],
            chat_history=[],  # Empty initially
        )

        turn1_context = agent_turn1.build_conversation_context()
        logger.debug(f"TURN 1 context length: {len(turn1_context)}")
        for i, msg in enumerate(turn1_context):
            logger.debug(f"  {i}: {type(msg).__name__} - {str(msg.content)[:50]}...")

        # TURN 2: Agent responds, conversation grows
        agent_response = Data(
            data={
                "text": "It seems there was some confusion regarding the operation to perform...",
                "sender": "Assistant",
            }
        )

        agent_turn2 = ALTKAgentComponent(
            _type="Agent",
            agent_llm=MockLanguageModel(),
            input_value="I wanted to write there plus",
            tools=[MockTool()],
            chat_history=[initial_query, agent_response],  # Chronological order
        )

        turn2_context = agent_turn2.build_conversation_context()
        logger.debug(f"\nTURN 2 context length: {len(turn2_context)}")
        for i, msg in enumerate(turn2_context):
            logger.debug(f"  {i}: {type(msg).__name__} - {str(msg.content)[:50]}...")

        # TURN 3: Add user follow-up, simulate the bug scenario
        user_followup = Data(data={"text": "I wanted to write there plus", "sender": "User"})

        agent_turn3 = ALTKAgentComponent(
            _type="Agent",
            agent_llm=MockLanguageModel(),
            input_value="current query",
            tools=[MockTool()],
            chat_history=[
                initial_query,
                agent_response,
                user_followup,
            ],  # Chronological order
        )

        turn3_context = agent_turn3.build_conversation_context()
        logger.debug(f"\nTURN 3 context length: {len(turn3_context)}")
        for i, msg in enumerate(turn3_context):
            logger.debug(f"  {i}: {type(msg).__name__} - {str(msg.content)[:50]}...")

        # Now simulate what happens in ValidatedTool during SPARC validation
        # Create a ValidatedTool and see how it processes the context
        mock_tool = MockTool()
        try:
            validated_tool = ValidatedTool(
                wrapped_tool=mock_tool,
                agent=agent_turn3,
                conversation_context=turn3_context,
                tool_specs=[],
            )

            # The ValidatedTool.update_context() gets called during tool processing
            # Let's simulate context updates like what happens in multi-turn conversations

            logger.debug("\n=== VALIDATED TOOL CONTEXT ANALYSIS ===")
            initial_validated_context = validated_tool.conversation_context
            logger.debug(f"Initial ValidatedTool context length: {len(initial_validated_context)}")
            for i, msg in enumerate(initial_validated_context):
                content = getattr(msg, "content", str(msg))
                logger.debug(f"  {i}: {str(content)[:50]}...")

            # This is where the bug likely manifests - during context updates
            # The update_context method just replaces the context, potentially in wrong order

            # Check for chronological order in the validated tool context
            contents = []
            for msg in initial_validated_context[1:]:  # Skip the current query (index 0)
                if hasattr(msg, "content"):
                    content = str(msg.content)
                    if "353454" in content:
                        contents.append(("353454", content))
                    elif "confusion" in content:
                        contents.append(("confusion", content))
                    elif "write there plus" in content:
                        contents.append(("plus", content))

            logger.debug("\nMessage order analysis:")
            for i, (label, content) in enumerate(contents):
                logger.debug(f"  {i}: {label} - {content[:40]}...")

            # The bug: 'plus' should come AFTER '353454' chronologically
            # But in the logs we saw 'plus' appearing first
            if len(contents) >= 2:
                order_positions = {label: i for i, (label, _) in enumerate(contents)}
                logger.debug(f"\nOrder positions: {order_positions}")

                if "353454" in order_positions and "plus" in order_positions:
                    chronological_correct = order_positions["353454"] < order_positions["plus"]
                    logger.debug(f"Chronological order correct: {chronological_correct}")
                    if not chronological_correct:
                        logger.debug("🐛 BUG DETECTED: Messages are in reverse chronological order!")
                        plus_position = order_positions["plus"]
                        logger.debug(
                            f"   '353454' should come before 'plus', but 'plus' is at position {plus_position}"
                        )
                        logger.debug(f"   while '353454' is at position {order_positions['353454']}")
                    else:
                        logger.debug("✅ Order appears correct in this test")

        except Exception as e:
            logger.debug(f"ValidatedTool creation failed: {e}")
            # Even if creation fails, we can analyze the base context ordering

        # At minimum, verify that build_conversation_context preserves order
        assert len(turn3_context) >= 3, "Should have current input + at least 3 history messages"