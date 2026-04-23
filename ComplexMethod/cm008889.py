def test_read_with_offset_and_limit(
        self, sandbox_backend: SandboxBackendProtocol, sandbox_test_root: str
    ) -> None:
        """Reading with offset and limit should return the expected slice."""
        if not self.has_sync:
            pytest.skip("Sync tests not supported.")

        test_path = self.sandbox_path(
            "offset_limit_test.txt", root_dir=sandbox_test_root
        )
        content = "\n".join([f"Row_{i}_content" for i in range(1, 21)])
        sandbox_backend.write(test_path, content)

        result = sandbox_backend.read(test_path, offset=10, limit=5)

        assert result.error is None
        assert result.file_data is not None
        assert "Row_11_content" in result.file_data["content"]
        assert "Row_15_content" in result.file_data["content"]
        assert "Row_10_content" not in result.file_data["content"]
        assert "Row_16_content" not in result.file_data["content"]