def test_edit_single_occurrence(
        self, sandbox_backend: SandboxBackendProtocol, sandbox_test_root: str
    ) -> None:
        """Edit a file and assert exactly one occurrence was replaced."""
        if not self.has_sync:
            pytest.skip("Sync tests not supported.")
        test_path = self.sandbox_path("edit_single.txt", root_dir=sandbox_test_root)
        content = "Hello world\nGoodbye world\nHello again"
        sandbox_backend.write(test_path, content)
        result = sandbox_backend.edit(test_path, "Goodbye", "Farewell")
        assert result.error is None
        assert result.occurrences == 1
        file_result = sandbox_backend.read(test_path)
        assert isinstance(file_result, ReadResult)
        assert file_result.error is None
        assert file_result.file_data is not None
        assert "Farewell world" in file_result.file_data["content"]
        assert "Goodbye" not in file_result.file_data["content"]