async def test_awrite_aread_large_text_payload(
        self, sandbox_backend: SandboxBackendProtocol, sandbox_test_root: str
    ) -> None:
        """Async write should allow a large text file to be read back non-empty."""
        if not self.has_async:
            pytest.skip("Async tests not supported.")

        test_path = self.sandbox_path(
            "large_async_text.txt", root_dir=sandbox_test_root
        )
        line = "0123456789abcdef" * 256
        lines = [line for _ in range(2560)]
        test_content = "\n".join(lines)

        write_result = await sandbox_backend.awrite(test_path, test_content)
        assert write_result.error is None
        assert write_result.path == test_path

        exec_result = await sandbox_backend.aexecute(f"wc -c {_quote(test_path)}")
        assert exec_result.exit_code == 0
        assert str(len(test_content.encode("utf-8"))) in exec_result.output

        read_result = await sandbox_backend.aread(test_path)
        assert isinstance(read_result, ReadResult)
        assert read_result.error is None
        assert read_result.file_data is not None
        assert read_result.file_data["encoding"] == "utf-8"
        assert read_result.file_data["content"].startswith(lines[0])