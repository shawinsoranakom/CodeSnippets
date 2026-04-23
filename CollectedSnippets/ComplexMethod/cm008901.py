def test_glob_with_directories(
        self, sandbox_backend: SandboxBackendProtocol, sandbox_test_root: str
    ) -> None:
        """Glob should include directories and mark them with `is_dir`."""
        if not self.has_sync:
            pytest.skip("Sync tests not supported.")

        base_dir = self.sandbox_path("glob_dirs", root_dir=sandbox_test_root)
        sandbox_backend.execute(
            f"mkdir -p {_quote(base_dir)}/dir1 {_quote(base_dir)}/dir2"
        )
        sandbox_backend.write(f"{base_dir}/file.txt", "content")

        result = sandbox_backend.glob("*", path=base_dir)

        assert result.error is None
        assert result.matches is not None
        assert len(result.matches) == 3
        dir_count = sum(1 for info in result.matches if info["is_dir"])
        file_count = sum(1 for info in result.matches if not info["is_dir"])
        assert dir_count == 2
        assert file_count == 1