async def test_aexecute_large_stdout_payload(
        self, sandbox_backend: SandboxBackendProtocol
    ) -> None:
        """Async execute should handle five parallel 500 KiB stdout commands."""
        if not self.has_async:
            pytest.skip("Async tests not supported.")

        command = "python -c \"import sys; sys.stdout.write('x' * (500 * 1024))\""
        if sys.version_info >= (3, 11):
            tasks: list[asyncio.Task[ExecuteResponse]] = []
            async with asyncio.TaskGroup() as tg:
                tasks.extend(
                    tg.create_task(sandbox_backend.aexecute(command)) for _ in range(5)
                )

            for task in tasks:
                result = task.result()
                assert result.exit_code == 0
                assert result.truncated is False
                assert len(result.output) >= 500 * 1024
                assert result.output.startswith("x")
        else:
            pytest.skip("asyncio.TaskGroup requires Python 3.11+")