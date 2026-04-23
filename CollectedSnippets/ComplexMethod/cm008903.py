def test_glob_with_question_mark(
        self, sandbox_backend: SandboxBackendProtocol, sandbox_test_root: str
    ) -> None:
        """Glob should support single-character wildcards."""
        if not self.has_sync:
            pytest.skip("Sync tests not supported.")

        base_dir = self.sandbox_path("glob_question", root_dir=sandbox_test_root)
        sandbox_backend.execute(f"mkdir -p {_quote(base_dir)}")
        sandbox_backend.write(f"{base_dir}/file1.txt", "content")
        sandbox_backend.write(f"{base_dir}/file2.txt", "content")
        sandbox_backend.write(f"{base_dir}/file10.txt", "content")

        result = sandbox_backend.glob("file?.txt", path=base_dir)

        assert result.error is None
        assert result.matches is not None
        paths = [info["path"] for info in result.matches]
        assert len(paths) == 2
        assert "file1.txt" in paths
        assert "file2.txt" in paths
        assert "file10.txt" not in paths