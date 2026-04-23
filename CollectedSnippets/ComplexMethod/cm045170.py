async def test_download_files() -> None:
    assert POOL_ENDPOINT is not None
    test_file_1 = "test1.txt"
    test_file_1_contents = "azure test file 1"
    test_file_2 = "test2"
    test_file_2_contents = "azure test file 2"
    cancellation_token = CancellationToken()

    with tempfile.TemporaryDirectory() as temp_dir:
        executor = ACADynamicSessionsCodeExecutor(
            pool_management_endpoint=POOL_ENDPOINT, credential=DefaultAzureCredential(), work_dir=temp_dir
        )
        await executor.start()

        code_blocks = [
            CodeBlock(
                code=f"""
with open("{test_file_1}", "w") as f:
    f.write("{test_file_1_contents}")
with open("{test_file_2}", "w") as f:
    f.write("{test_file_2_contents}")
""",
                language="python",
            ),
        ]
        code_result = await executor.execute_code_blocks(code_blocks, cancellation_token)
        assert code_result.exit_code == 0

        file_list = await executor.get_file_list(cancellation_token)
        assert test_file_1 in file_list
        assert test_file_2 in file_list

        await executor.download_files([test_file_1, test_file_2], cancellation_token)

        assert os.path.isfile(os.path.join(temp_dir, test_file_1))
        async with await open_file(os.path.join(temp_dir, test_file_1), "r") as f:
            content = await f.read()
            assert test_file_1_contents in content
        assert os.path.isfile(os.path.join(temp_dir, test_file_2))
        async with await open_file(os.path.join(temp_dir, test_file_2), "r") as f:
            content = await f.read()
            assert test_file_2_contents in content

        await executor.stop()