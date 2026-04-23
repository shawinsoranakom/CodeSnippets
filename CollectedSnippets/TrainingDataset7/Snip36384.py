def test_format_html_join_with_positional_arguments(self):
        self.assertEqual(
            format_html_join(
                "\n",
                "<li>{}) {}</li>",
                [(1, "Emma"), (2, "Matilda")],
            ),
            "<li>1) Emma</li>\n<li>2) Matilda</li>",
        )