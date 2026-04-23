def test_render_boolean(self):
        """
        Boolean values are rendered to their string forms ("True" and
        "False").
        """
        self.check_html(
            self.widget,
            "get_spam",
            False,
            html=('<input type="text" name="get_spam" value="False">'),
        )
        self.check_html(
            self.widget,
            "get_spam",
            True,
            html=('<input type="text" name="get_spam" value="True">'),
        )