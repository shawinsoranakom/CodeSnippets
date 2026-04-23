async def test_aread_large_text_payload_paginated_roundtrip(
        self, sandbox_backend: SandboxBackendProtocol, sandbox_test_root: str
    ) -> None:
        """Async paginated reads should reconstruct the full large text payload."""
        if not self.has_async:
            pytest.skip("Async tests not supported.")

        test_path = self.sandbox_path(
            "large_async_chunked.txt", root_dir=sandbox_test_root
        )
        lines = [f"Line_{i:04d}_content" for i in range(2500)]
        test_content = "\n".join(lines)

        write_result = await sandbox_backend.awrite(test_path, test_content)
        assert write_result.error is None

        parts: list[str] = []
        for offset in range(0, len(lines), 100):
            page = await sandbox_backend.aread(test_path, offset=offset, limit=100)
            assert page.error is None
            assert page.file_data is not None
            assert page.file_data["content"] == "\n".join(lines[offset : offset + 100])
            parts.append(page.file_data["content"])

        assert "\n".join(parts) == test_content