def test_check_title_with_markdown_syntax_incorrect(self):
        self.assertEqual(err_msg, expected_err_msg)

    def test_check_title_with_api_at_the_end_of_the_title(self):
        raw_title = '[A API](https://www.ex.com)'

        err_msgs = check_title(0, raw_title)
        
        self.assertIsInstance(err_msgs, list)
        self.assertEqual(len(err_msgs), 1)
        
        err_msg = err_msgs[0]
        expected_err_msg = '(L001) Title should not end with "... API". Every entry is an API here!'

        self.assertEqual(err_msg, expected_err_msg)
