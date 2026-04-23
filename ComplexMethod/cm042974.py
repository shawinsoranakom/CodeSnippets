def test_shrink_default_subdirectory_structure(self, tmp_path):
        """Test shrinking when profile has Default/ subdirectory."""
        profile = tmp_path / "profile"
        profile.mkdir()

        # Chrome-style structure with Default/
        default = profile / "Default"
        default.mkdir()
        (default / "Local Storage").mkdir()
        (default / "Local Storage" / "leveldb").mkdir()
        (default / "Cookies").write_bytes(b"cookies" * 100)
        (default / "Cache").mkdir()
        (default / "Cache" / "data").write_bytes(b"x" * 10000)
        (default / "GPUCache").mkdir()
        (default / "GPUCache" / "data").write_bytes(b"y" * 5000)

        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)

        # Should shrink inside Default/
        assert "Cache" in result["removed"]
        assert "GPUCache" in result["removed"]
        assert "Local Storage" in result["kept"]
        assert "Cookies" in result["kept"]
        assert (default / "Local Storage").exists()
        assert (default / "Cookies").exists()
        assert not (default / "Cache").exists()