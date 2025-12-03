 def test_check_file_format_without_1_space_between_the_segments(self):
        incorrect_format = [
            '## Index',
            '* [A](#a)',
            '',
            '### A',
            'API | Description | Auth | HTTPS | CORS |',
            '|---|---|---|---|---|',
            '| [AA](https://www.ex.com) | Desc |`apiKey`| Yes | Yes |',  # space between segment of auth column missing
            '| [AB](https://www.ex.com) | Desc | `apiKey` | Yes | Yes |',
            '| [AC](https://www.ex.com) | Desc | `apiKey` | Yes | Yes |',
        ]

        err_msgs = check_file_format(lines=incorrect_format)
        expected_err_msg = f'(L007) each segment must start and end with exactly 1 space'

        self.assertIsInstance(err_msgs, list)
        self.assertEqual(len(err_msgs), 1)
        err_msg = err_msgs[0]
        self.assertEqual(err_msg, expected_err_msg)
