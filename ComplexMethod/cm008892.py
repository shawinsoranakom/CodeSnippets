def test_read_very_large_file_in_chunks(
        self, sandbox_backend: SandboxBackendProtocol, sandbox_test_root: str
    ) -> None:
        """Repeated offset+limit reads should cover different slices of a large file."""
        if not self.has_sync:
            pytest.skip("Sync tests not supported.")

        test_path = self.sandbox_path("large_chunked.txt", root_dir=sandbox_test_root)
        content = "\n".join([f"Line_{i:04d}_content" for i in range(1000)])
        sandbox_backend.write(test_path, content)

        first = sandbox_backend.read(test_path, offset=0, limit=100)
        middle = sandbox_backend.read(test_path, offset=500, limit=100)
        last = sandbox_backend.read(test_path, offset=900, limit=100)

        assert first.error is None
        assert first.file_data is not None
        assert "Line_0000_content" in first.file_data["content"]
        assert "Line_0099_content" in first.file_data["content"]
        assert "Line_0100_content" not in first.file_data["content"]

        assert middle.error is None
        assert middle.file_data is not None
        assert "Line_0500_content" in middle.file_data["content"]
        assert "Line_0599_content" in middle.file_data["content"]
        assert "Line_0499_content" not in middle.file_data["content"]

        assert last.error is None
        assert last.file_data is not None
        assert "Line_0900_content" in last.file_data["content"]
        assert "Line_0999_content" in last.file_data["content"]