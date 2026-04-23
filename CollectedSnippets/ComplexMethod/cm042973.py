def test_shrink_aggressive_removes_caches(self, mock_profile):
        result = shrink_profile(mock_profile, ShrinkLevel.AGGRESSIVE)

        # Auth data kept
        assert "Network" in result["kept"]
        assert "Local Storage" in result["kept"]
        assert "IndexedDB" in result["kept"]
        assert "Preferences" in result["kept"]

        # Caches removed
        assert "Cache" in result["removed"]
        assert "Code Cache" in result["removed"]
        assert "GPUCache" in result["removed"]
        assert "Service Worker" in result["removed"]

        # Verify bytes freed > 0
        assert result["bytes_freed"] > 0
        assert result["size_after"] < result["size_before"]