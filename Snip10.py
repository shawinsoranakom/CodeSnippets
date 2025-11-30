 def test_check_file_format_entry_without_all_necessary_columns(self):
        incorrect_format = [
            '## Index',
            '* [A](#a)',
            '',
            '### A',
            'API | Description | Auth | HTTPS | CORS |',
            '|---|---|---|---|---|',
            '| [AA](https://www.ex.com) | Desc | `apiKey` | Yes | Yes |',
            '| [AB](https://www.ex.com) | Desc | `apiKey` |',  # missing https and cors
            '| [AC](https://www.ex.com) | Desc | `apiKey` | Yes | Yes |',
        ]

        current_segments_num = 3

        err_msgs = check_file_format(lines=incorrect_format)
        expected_err_msg = f'(L008) entry does not have all the required columns (have {current_segments_num}, need {num_segments})'

        self.assertIsInstance(err_msgs, list)
        self.assertEqual(len(err_msgs), 1)
        err_msg = err_msgs[0]
        self.assertEqual(err_msg, expected_err_msg)
