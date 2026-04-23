def test_grep_basic_search(
        self, sandbox_backend: SandboxBackendProtocol, sandbox_test_root: str
    ) -> None:
        """Grep should return matches across multiple files."""
        if not self.has_sync:
            pytest.skip("Sync tests not supported.")

        base_dir = self.sandbox_path("grep_test", root_dir=sandbox_test_root)
        sandbox_backend.execute(f"mkdir -p {_quote(base_dir)}")
        sandbox_backend.write(f"{base_dir}/file1.txt", "Hello world\nGoodbye world")
        sandbox_backend.write(f"{base_dir}/file2.txt", "Hello there\nGoodbye friend")

        result = sandbox_backend.grep("Hello", path=base_dir)

        assert result.error is None
        assert result.matches is not None
        assert len(result.matches) == 2
        paths = [match["path"] for match in result.matches]
        assert any(path.endswith("file1.txt") for path in paths)
        assert any(path.endswith("file2.txt") for path in paths)
        assert all(match["line"] == 1 for match in result.matches)