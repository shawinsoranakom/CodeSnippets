def test_glob_with_character_class(
        self, sandbox_backend: SandboxBackendProtocol, sandbox_test_root: str
    ) -> None:
        """Glob should support character classes in patterns."""
        if not self.has_sync:
            pytest.skip("Sync tests not supported.")

        base_dir = self.sandbox_path("glob_charclass", root_dir=sandbox_test_root)
        sandbox_backend.execute(f"mkdir -p {_quote(base_dir)}")
        sandbox_backend.write(f"{base_dir}/file1.txt", "content")
        sandbox_backend.write(f"{base_dir}/file2.txt", "content")
        sandbox_backend.write(f"{base_dir}/file3.txt", "content")
        sandbox_backend.write(f"{base_dir}/fileA.txt", "content")

        result = sandbox_backend.glob("file[1-2].txt", path=base_dir)

        assert result.error is None
        assert result.matches is not None
        paths = [info["path"] for info in result.matches]
        assert len(paths) == 2
        assert "file1.txt" in paths
        assert "file2.txt" in paths
        assert "file3.txt" not in paths
        assert "fileA.txt" not in paths