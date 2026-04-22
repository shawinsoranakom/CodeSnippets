def test_clear_all_disk_caches(self, mock_rmtree):
        """`clear_all` should remove the disk cache directory if it exists."""

        # If the cache dir exists, we should delete it.
        with patch("os.path.isdir", MagicMock(return_value=True)):
            st.experimental_memo.clear()
            mock_rmtree.assert_called_once_with(get_cache_path())

        mock_rmtree.reset_mock()

        # If the cache dir does not exist, we shouldn't try to delete it.
        with patch("os.path.isdir", MagicMock(return_value=False)):
            st.experimental_memo.clear()
            mock_rmtree.assert_not_called()