def test_read_offset_at_exact_file_length(
        self, sandbox_backend: SandboxBackendProtocol, sandbox_test_root: str
    ) -> None:
        """Reading exactly at EOF should return no file lines."""
        if not self.has_sync:
            pytest.skip("Sync tests not supported.")

        test_path = self.sandbox_path("offset_exact.txt", root_dir=sandbox_test_root)
        content = "\n".join([f"Line {i}" for i in range(1, 6)])
        sandbox_backend.write(test_path, content)

        result = sandbox_backend.read(test_path, offset=5, limit=10)

        text = result.file_data["content"] if result.file_data else ""
        error = result.error or ""
        assert "Line 1" not in text
        assert "Line 1" not in error
        assert "Line 5" not in text
        assert "Line 5" not in error