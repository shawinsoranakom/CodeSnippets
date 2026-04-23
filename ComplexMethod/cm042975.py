def test_shrink_mixed_files_and_directories(self, tmp_path):
        """Test shrinking mix of files and directories."""
        profile = tmp_path / "profile"
        profile.mkdir()

        (profile / "Local Storage").mkdir()
        (profile / "Preferences").write_text("{}")
        (profile / "Cookies").write_bytes(b"x" * 500)
        (profile / "Cookies-journal").write_bytes(b"y" * 100)
        (profile / "History").write_bytes(b"z" * 1000)
        (profile / "Cache").mkdir()
        (profile / "random_file.txt").write_bytes(b"a" * 200)

        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)

        # Files and dirs properly categorized
        assert "Local Storage" in result["kept"]
        assert "Preferences" in result["kept"]
        assert "Cookies" in result["kept"]
        assert "Cookies-journal" in result["kept"]
        assert "History" in result["removed"]
        assert "Cache" in result["removed"]
        assert "random_file.txt" in result["removed"]