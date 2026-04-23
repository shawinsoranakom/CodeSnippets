def test_url_as_property(self):
        class URLFieldFile:
            @property
            def url(self):
                return "https://www.python.org/"

            def __str__(self):
                return "value"

        html = self.widget.render("myfile", URLFieldFile())
        self.assertInHTML('<a href="https://www.python.org/">value</a>', html)