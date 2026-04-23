def test_edit_special_characters(
        self, sandbox_backend: SandboxBackendProtocol, sandbox_test_root: str
    ) -> None:
        """Editing should treat special characters as literal strings."""
        if not self.has_sync:
            pytest.skip("Sync tests not supported.")

        test_path = self.sandbox_path("edit_special.txt", root_dir=sandbox_test_root)
        content = "Price: $100.00\nPattern: [a-z]*\nPath: /usr/bin"
        sandbox_backend.write(test_path, content)

        first = sandbox_backend.edit(test_path, "$100.00", "$200.00")
        second = sandbox_backend.edit(test_path, "[a-z]*", "[0-9]+")

        assert first.error is None
        assert second.error is None
        read_result = sandbox_backend.read(test_path)
        assert read_result.error is None
        assert read_result.file_data is not None
        assert "$200.00" in read_result.file_data["content"]
        assert "[0-9]+" in read_result.file_data["content"]