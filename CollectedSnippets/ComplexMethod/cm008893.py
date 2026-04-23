def test_edit_multiple_occurrences_without_replace_all(
        self, sandbox_backend: SandboxBackendProtocol, sandbox_test_root: str
    ) -> None:
        """Editing multiple matches without `replace_all` should fail."""
        if not self.has_sync:
            pytest.skip("Sync tests not supported.")

        test_path = self.sandbox_path("edit_multi.txt", root_dir=sandbox_test_root)
        content = "apple\nbanana\napple\norange\napple"
        sandbox_backend.write(test_path, content)

        result = sandbox_backend.edit(test_path, "apple", "pear", replace_all=False)

        assert result.error is not None
        assert "multiple" in result.error.lower()
        read_result = sandbox_backend.read(test_path)
        assert read_result.error is None
        assert read_result.file_data is not None
        assert "apple" in read_result.file_data["content"]
        assert "pear" not in read_result.file_data["content"]