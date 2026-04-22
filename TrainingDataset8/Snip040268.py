def test_cache_clear_command_without_cache(self, mock_print):
        """Tests clear cache announces when there is nothing to clear"""
        with patch(
            "streamlit.runtime.legacy_caching.clear_cache", return_value=False
        ) as mock_clear_cache:
            self.runner.invoke(cli, ["cache", "clear"])
            mock_clear_cache.assert_called()
            first_call = mock_print.call_args[0]
            first_arg = first_call[0]
            self.assertTrue(first_arg.startswith("Nothing to clear"))