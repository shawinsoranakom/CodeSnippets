def test_edit_multiple_occurrences_with_replace_all(
        self, sandbox_backend: SandboxBackendProtocol, sandbox_test_root: str
    ) -> None:
        """Editing multiple matches with `replace_all` should replace each match."""
        if not self.has_sync:
            pytest.skip("Sync tests not supported.")

        test_path = self.sandbox_path(
            "edit_replace_all.txt", root_dir=sandbox_test_root
        )
        content = "apple\nbanana\napple\norange\napple"
        sandbox_backend.write(test_path, content)

        result = sandbox_backend.edit(test_path, "apple", "pear", replace_all=True)

        assert result.error is None
        assert result.occurrences == 3
        read_result = sandbox_backend.read(test_path)
        assert read_result.error is None
        assert read_result.file_data is not None
        assert "apple" not in read_result.file_data["content"]
        assert read_result.file_data["content"].count("pear") == 3