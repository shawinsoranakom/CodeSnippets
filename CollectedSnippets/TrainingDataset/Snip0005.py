def test_if_get_categories_content_return_correct_data_of_categories(self):
        fake_contents = [
            '### A',
            'API | Description | Auth | HTTPS | CORS |',
            '|---|---|---|---|---|',
            '| [AA](https://www.ex.com) | Desc | `apiKey` | Yes | Yes |',
            '| [AB](https://www.ex.com) | Desc | `apiKey` | Yes | Yes |',
            '',
            '### B',
            'API | Description | Auth | HTTPS | CORS |',
            '|---|---|---|---|---|',
            '| [BA](https://www.ex.com) | Desc | `apiKey` | Yes | Yes |',
            '| [BB](https://www.ex.com) | Desc | `apiKey` | Yes | Yes |'
        ]

        result = get_categories_content(fake_contents)
        self.assertIsInstance(result, tuple)

        categories, category_line_num = result
        self.assertIsInstance(categories, dict)
        self.assertIsInstance(category_line_num, dict)

        expected_result = ({'A': ['AA', 'AB'], 'B': ['BA', 'BB']}, {'A': 0, 'B': 6})

        for res, ex_res in zip(result, expected_result):

            with self.subTest():
                self.assertEqual(res, ex_res)
