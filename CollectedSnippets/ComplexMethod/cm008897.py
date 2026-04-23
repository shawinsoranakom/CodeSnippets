def test_ls_special_characters_in_filenames(
        self, sandbox_backend: SandboxBackendProtocol, sandbox_test_root: str
    ) -> None:
        """Listing should preserve filenames with shell metacharacters."""
        if not self.has_sync:
            pytest.skip("Sync tests not supported.")

        base_dir = self.sandbox_path("ls_special", root_dir=sandbox_test_root)
        sandbox_backend.execute(f"mkdir -p {_quote(base_dir)}")
        sandbox_backend.write(f"{base_dir}/file(1).txt", "content")
        sandbox_backend.write(f"{base_dir}/file[2].txt", "content")
        sandbox_backend.write(f"{base_dir}/file-3.txt", "content")

        result = sandbox_backend.ls(base_dir)

        assert result.error is None
        assert result.entries is not None
        paths = [entry["path"] for entry in result.entries]
        assert f"{base_dir}/file(1).txt" in paths
        assert f"{base_dir}/file[2].txt" in paths
        assert f"{base_dir}/file-3.txt" in paths