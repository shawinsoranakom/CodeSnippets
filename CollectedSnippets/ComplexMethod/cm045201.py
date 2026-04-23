async def test_python_code_execution_tool(caplog: pytest.LogCaptureFixture) -> None:
    """Test basic functionality of PythonCodeExecutionTool."""
    # Create a temporary directory for the executor
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize the executor and tool
        executor = LocalCommandLineCodeExecutor(work_dir=temp_dir)
        tool = PythonCodeExecutionTool(executor=executor)

        with caplog.at_level(logging.INFO):
            # Test simple code execution
            code = "print('hello world!')"
            result = await tool.run_json(args={"code": code}, cancellation_token=CancellationToken())
            # Check log output
            assert "hello world!" in caplog.text

        # Verify successful execution
        assert result.success is True
        assert "hello world!" in result.output

        # Test code with computation
        code = """a = 100 + 200 \nprint(f'Result: {a}')
        """
        result = await tool.run(args=CodeExecutionInput(code=code), cancellation_token=CancellationToken())

        # Verify computation result
        assert result.success is True
        assert "Result: 300" in result.output

        # Test error handling
        code = "print(undefined_variable)"
        result = await tool.run(args=CodeExecutionInput(code=code), cancellation_token=CancellationToken())

        # Verify error handling
        assert result.success is False
        assert "NameError" in result.output