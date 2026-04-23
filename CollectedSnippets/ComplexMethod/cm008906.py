def test_write_read_download_large_text_with_escaped_content(
        self, sandbox_backend: SandboxBackendProtocol, sandbox_test_root: str
    ) -> None:
        """Sync large-text roundtrips should preserve escaped and unicode content."""
        if not self.has_sync:
            pytest.skip("Sync tests not supported.")

        test_path = self.sandbox_path(
            "large_sync_escaped.txt", root_dir=sandbox_test_root
        )
        line = (
            "prefix\t\u2603\u4e16\u754c\u03c0\u22483.14159"
            " | spaces   preserved"
            " | quotes ' \""
            " | brackets [] {{}}"
            " | shell $VAR `cmd` $(subshell)"
            " | slash /tmp/path and backslash \\\\"
            " | control-ish \\r \\n"
            " | suffix"
        )
        lines = [f"{i:04d}:{line}" for i in range(2500)]
        test_content = "\n".join(lines)

        write_result = sandbox_backend.write(test_path, test_content)
        assert write_result.error is None

        pages: list[str] = []
        for offset in range(0, len(lines), 100):
            page = sandbox_backend.read(test_path, offset=offset, limit=100)
            assert page.error is None
            assert page.file_data is not None
            assert page.file_data["content"] == "\n".join(lines[offset : offset + 100])
            pages.append(page.file_data["content"])

        assert "\n".join(pages) == test_content

        download_responses = sandbox_backend.download_files([test_path])
        assert download_responses == [
            FileDownloadResponse(
                path=test_path,
                content=test_content.encode("utf-8"),
                error=None,
            )
        ]