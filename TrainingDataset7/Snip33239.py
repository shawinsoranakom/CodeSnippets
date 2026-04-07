def test_caching_repeated_calls(self, mock_handle_word):
        urlize("test")
        handle_word_test = mock.call(
            "test",
            safe_input=False,
            trim_url_limit=None,
            nofollow=True,
            autoescape=True,
        )
        self.assertEqual(mock_handle_word.mock_calls, [handle_word_test])

        urlize("test")
        self.assertEqual(
            mock_handle_word.mock_calls, [handle_word_test, handle_word_test]
        )