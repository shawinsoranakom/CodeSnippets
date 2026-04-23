def test_cache_clear_command_with_cache(self, mock_print):
        """Tests clear cache announces that cache is cleared when completed"""
        with patch(
            "streamlit.runtime.legacy_caching.clear_cache", return_value=True
        ) as mock_clear_cache:
            self.runner.invoke(cli, ["cache", "clear"])
            mock_clear_cache.assert_called()
            first_call = mock_print.call_args[0]
            first_arg = first_call[0]
            self.assertTrue(first_arg.startswith("Cleared directory"))