def test_format_html_join_with_keyword_arguments(self):
        self.assertEqual(
            format_html_join(
                "\n",
                "<li>{id}) {text}</li>",
                [{"id": 1, "text": "Emma"}, {"id": 2, "text": "Matilda"}],
            ),
            "<li>1) Emma</li>\n<li>2) Matilda</li>",
        )