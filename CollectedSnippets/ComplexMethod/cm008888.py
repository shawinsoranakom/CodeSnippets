def test_read_with_limit(
        self, sandbox_backend: SandboxBackendProtocol, sandbox_test_root: str
    ) -> None:
        """Reading with limit should cap the number of returned lines."""
        if not self.has_sync:
            pytest.skip("Sync tests not supported.")

        test_path = self.sandbox_path("limit_test.txt", root_dir=sandbox_test_root)
        content = "\n".join([f"Row_{i}_content" for i in range(1, 101)])
        sandbox_backend.write(test_path, content)

        result = sandbox_backend.read(test_path, offset=0, limit=5)

        assert result.error is None
        assert result.file_data is not None
        assert "Row_1_content" in result.file_data["content"]
        assert "Row_5_content" in result.file_data["content"]
        assert "Row_6_content" not in result.file_data["content"]