def test_read_offset_beyond_file_length(
        self, sandbox_backend: SandboxBackendProtocol, sandbox_test_root: str
    ) -> None:
        """Reading beyond EOF should return no file lines."""
        if not self.has_sync:
            pytest.skip("Sync tests not supported.")

        test_path = self.sandbox_path("offset_beyond.txt", root_dir=sandbox_test_root)
        sandbox_backend.write(test_path, "Line 1\nLine 2\nLine 3")

        result = sandbox_backend.read(test_path, offset=100, limit=10)

        content = result.file_data["content"] if result.file_data else ""
        error = result.error or ""
        assert "Line 1" not in content
        assert "Line 1" not in error
        assert "Line 2" not in content
        assert "Line 2" not in error
        assert "Line 3" not in content
        assert "Line 3" not in error