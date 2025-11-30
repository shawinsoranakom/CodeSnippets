def test_check_title_with_markdown_syntax_incorrect(self):
        raw_title = '[A(https://www.ex.com)'

        err_msgs = check_title(0, raw_title)

        self.assertIsInstance(err_msgs, list)
        self.assertEqual(len(err_msgs), 1)
        
        err_msg = err_msgs[0]
        expected_err_msg = '(L001) Title syntax should be "[TITLE](LINK)"'

        self.assertEqual(err_msg, expected_err_msg)
