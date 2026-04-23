def test_glob_basic_pattern(
        self, sandbox_backend: SandboxBackendProtocol, sandbox_test_root: str
    ) -> None:
        """Glob should match basic wildcard patterns."""
        if not self.has_sync:
            pytest.skip("Sync tests not supported.")

        base_dir = self.sandbox_path("glob_test", root_dir=sandbox_test_root)
        sandbox_backend.execute(f"mkdir -p {_quote(base_dir)}")
        sandbox_backend.write(f"{base_dir}/file1.txt", "content")
        sandbox_backend.write(f"{base_dir}/file2.txt", "content")
        sandbox_backend.write(f"{base_dir}/file3.py", "content")

        result = sandbox_backend.glob("*.txt", path=base_dir)

        assert result.error is None
        assert result.matches is not None
        paths = [info["path"] for info in result.matches]
        assert len(paths) == 2
        assert "file1.txt" in paths
        assert "file2.txt" in paths
        assert not any(path.endswith(".py") for path in paths)