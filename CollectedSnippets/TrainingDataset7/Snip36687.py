def test_truncate_chars_html_with_misnested_tags(self):
        # LIFO removal keeps all tags when a middle tag is closed out of order.
        # With <a><b><c></b>, the </b> doesn't match <c>, so all tags remain
        # in the stack and are properly closed at truncation.
        truncator = text.Truncator("<a><b><c></b>XXXX")
        self.assertEqual(
            truncator.chars(2, html=True, truncate=""),
            "<a><b><c></b>XX</c></b></a>",
        )