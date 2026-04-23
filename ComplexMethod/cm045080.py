def test_magentic_one_with_explicit_code_executor_and_approval_function(mock_chat_client: Mock) -> None:
    """Test that MagenticOne uses the provided code executor and approval function when explicitly given."""
    explicit_executor = LocalCommandLineCodeExecutor()

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        m1 = MagenticOne(
            client=mock_chat_client, code_executor=explicit_executor, approval_func=approval_function_allow_all
        )

        # Find the CodeExecutorAgent in the participants list
        code_executor_agent = None
        for agent in m1._participants:  # type: ignore[reportPrivateUsage]
            if isinstance(agent, CodeExecutorAgent):
                code_executor_agent = agent
                break

        assert code_executor_agent is not None, "CodeExecutorAgent not found"
        assert code_executor_agent._code_executor is explicit_executor, "Expected the explicitly provided code executor"  # type: ignore[reportPrivateUsage]

        # Test that approval function is set correctly
        assert code_executor_agent._approval_func is approval_function_allow_all, "Expected approval function to be set"  # type: ignore[reportPrivateUsage]

        # No deprecation warning should be issued when explicitly providing a code executor
        warning_messages = [str(warning.message) for warning in w]
        deprecated_warning_found = any(
            "Instantiating MagenticOne without a code_executor is deprecated" in msg for msg in warning_messages
        )

        assert not deprecated_warning_found, f"Unexpected deprecation warning found: {warning_messages}"