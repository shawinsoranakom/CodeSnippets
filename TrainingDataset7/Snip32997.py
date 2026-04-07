def test_lazy_string_input(self):
        add_header = lazy(lambda string: "Header\n\n" + string, str)
        self.assertEqual(
            linebreaks_filter(add_header("line 1\r\nline2")),
            "<p>Header</p>\n\n<p>line 1<br>line2</p>",
        )