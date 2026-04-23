async def test_cleanup_temp_files_behavior() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test with cleanup_temp_files=True (default)
        executor = LocalCommandLineCodeExecutor(work_dir=temp_dir, cleanup_temp_files=True)
        await executor.start()
        cancellation_token = CancellationToken()
        code_blocks = [CodeBlock(code="print('cleanup test')", language="python")]
        result = await executor.execute_code_blocks(code_blocks, cancellation_token)
        assert result.exit_code == 0
        assert "cleanup test" in result.output
        # The code file should have been deleted
        assert result.code_file is not None
        assert not Path(result.code_file).exists()

        # Test with cleanup_temp_files=False
        executor = LocalCommandLineCodeExecutor(work_dir=temp_dir, cleanup_temp_files=False)
        await executor.start()
        cancellation_token = CancellationToken()
        code_blocks = [CodeBlock(code="print('no cleanup')", language="python")]
        result = await executor.execute_code_blocks(code_blocks, cancellation_token)
        assert result.exit_code == 0
        assert "no cleanup" in result.output
        # The code file should still exist
        assert result.code_file is not None
        assert Path(result.code_file).exists()