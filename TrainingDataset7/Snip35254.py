def test_attributes(self):
        self.assertHTMLEqual(
            '<input type="text" id="id_name" />', '<input id="id_name" type="text" />'
        )
        self.assertHTMLEqual(
            """<input type='text' id="id_name" />""",
            '<input id="id_name" type="text" />',
        )
        self.assertHTMLNotEqual(
            '<input type="text" id="id_name" />',
            '<input type="password" id="id_name" />',
        )