def test_stylesheets_typeerror_if_str_or_stylesheet(self):
        for stylesheet, error_message in [
            ("/stylesheet.xsl", "stylesheets should be a list, not <class 'str'>"),
            (
                Stylesheet("/stylesheet.xsl"),
                "stylesheets should be a list, "
                "not <class 'django.utils.feedgenerator.Stylesheet'>",
            ),
        ]:
            args = ("title", "/link", "description")
            with self.subTest(stylesheets=stylesheet):
                self.assertRaisesMessage(
                    TypeError,
                    error_message,
                    SyndicationFeed,
                    *args,
                    stylesheets=stylesheet,
                )