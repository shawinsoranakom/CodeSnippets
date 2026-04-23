async def test_delete_tmp_files() -> None:
    if not docker_tests_enabled():
        pytest.skip("Docker tests are disabled")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Test with delete_tmp_files=False (default)
        async with DockerCommandLineCodeExecutor(work_dir=temp_dir) as executor:
            cancellation_token = CancellationToken()
            code_blocks = [CodeBlock(code="print('test output')", language="python")]
            result = await executor.execute_code_blocks(code_blocks, cancellation_token)
            assert result.exit_code == 0
            assert result.code_file is not None
            # Verify file exists after execution
            assert Path(result.code_file).exists()

        # Test with delete_tmp_files=True
        async with DockerCommandLineCodeExecutor(work_dir=temp_dir, delete_tmp_files=True) as executor:
            cancellation_token = CancellationToken()
            code_blocks = [CodeBlock(code="print('test output')", language="python")]
            result = await executor.execute_code_blocks(code_blocks, cancellation_token)
            assert result.exit_code == 0
            assert result.code_file is not None
            # Verify file is deleted after execution
            assert not Path(result.code_file).exists()

            # Test with multiple code blocks
            code_blocks = [
                CodeBlock(code="print('first block')", language="python"),
                CodeBlock(code="print('second block')", language="python"),
            ]
            result = await executor.execute_code_blocks(code_blocks, cancellation_token)
            assert result.exit_code == 0
            assert result.code_file is not None
            # Verify files are deleted after execution
            assert not Path(result.code_file).exists()

            # Test deletion with execution error
            code_blocks = [CodeBlock(code="raise Exception('test error')", language="python")]
            result = await executor.execute_code_blocks(code_blocks, cancellation_token)
            assert result.exit_code != 0
            assert result.code_file is not None
            # Verify file is deleted even after error
            assert not Path(result.code_file).exists()