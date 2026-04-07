def test_caching_repeated_words(self, mock_handle_word):
        urlize("test test test test")
        common_handle_word_args = {
            "safe_input": False,
            "trim_url_limit": None,
            "nofollow": True,
            "autoescape": True,
        }
        self.assertEqual(
            mock_handle_word.mock_calls,
            [
                mock.call("test", **common_handle_word_args),
                mock.call(" ", **common_handle_word_args),
            ],
        )