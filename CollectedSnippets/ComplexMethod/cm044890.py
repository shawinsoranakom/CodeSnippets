def test_install_copies_scripts(self, tmp_path: Path):
        """Extension install copies script files."""
        from specify_cli.extensions import ExtensionManager

        (tmp_path / ".specify").mkdir()
        manager = ExtensionManager(tmp_path)
        manager.install_from_directory(EXT_DIR, "0.5.0", register_commands=False)

        ext_installed = tmp_path / ".specify" / "extensions" / "git"
        assert (ext_installed / "scripts" / "bash" / "create-new-feature.sh").is_file()
        assert (ext_installed / "scripts" / "bash" / "initialize-repo.sh").is_file()
        assert (ext_installed / "scripts" / "bash" / "auto-commit.sh").is_file()
        assert (ext_installed / "scripts" / "bash" / "git-common.sh").is_file()
        assert (ext_installed / "scripts" / "powershell" / "create-new-feature.ps1").is_file()
        assert (ext_installed / "scripts" / "powershell" / "initialize-repo.ps1").is_file()
        assert (ext_installed / "scripts" / "powershell" / "auto-commit.ps1").is_file()
        assert (ext_installed / "scripts" / "powershell" / "git-common.ps1").is_file()