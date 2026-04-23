def test_magentic_one_falls_back_to_local_when_docker_unavailable(
    mock_docker_check: Mock, mock_chat_client: Mock
) -> None:
    """Test that MagenticOne falls back to local executor when Docker is not available."""
    mock_docker_check.return_value = False

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        m1 = MagenticOne(client=mock_chat_client)

        # Find the CodeExecutorAgent in the participants list
        code_executor_agent = None
        for agent in m1._participants:  # type: ignore[reportPrivateUsage]
            if isinstance(agent, CodeExecutorAgent):
                code_executor_agent = agent
                break

        assert code_executor_agent is not None, "CodeExecutorAgent not found"
        assert isinstance(
            code_executor_agent._code_executor,  # type: ignore[reportPrivateUsage]
            LocalCommandLineCodeExecutor,  # type: ignore[reportPrivateUsage]
        ), f"Expected LocalCommandLineCodeExecutor, got {type(code_executor_agent._code_executor)}"  # type: ignore[reportPrivateUsage]

        # Test that no approval function is set by default
        assert code_executor_agent._approval_func is None, "Expected no approval function by default"  # type: ignore[reportPrivateUsage]

        # Check that appropriate warnings were issued
        warning_messages = [str(warning.message) for warning in w]
        docker_warning_found = any("Docker is not available" in msg for msg in warning_messages)
        deprecated_warning_found = any(
            "Instantiating MagenticOne without a code_executor is deprecated" in msg for msg in warning_messages
        )

        assert docker_warning_found, f"Docker unavailable warning not found in: {warning_messages}"
        assert deprecated_warning_found, f"Deprecation warning not found in: {warning_messages}"