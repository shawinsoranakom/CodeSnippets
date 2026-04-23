def test_ls_large_directory(
        self, sandbox_backend: SandboxBackendProtocol, sandbox_test_root: str
    ) -> None:
        """Listing a larger directory should include all created entries."""
        if not self.has_sync:
            pytest.skip("Sync tests not supported.")

        base_dir = self.sandbox_path("ls_large", root_dir=sandbox_test_root)
        sandbox_backend.execute(
            f"mkdir -p {_quote(base_dir)} && "
            f"cd {_quote(base_dir)} && "
            "for i in $(seq 0 49); do "
            "echo content > file_$(printf '%03d' $i).txt; "
            "done"
        )

        result = sandbox_backend.ls(base_dir)

        assert result.error is None
        assert result.entries is not None
        assert len(result.entries) == 50
        paths = [entry["path"] for entry in result.entries]
        assert f"{base_dir}/file_000.txt" in paths
        assert f"{base_dir}/file_049.txt" in paths