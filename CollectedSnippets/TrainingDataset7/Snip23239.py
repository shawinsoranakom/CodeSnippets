def test_return_false_if_url_does_not_exists(self):
        class NoURLFieldFile:
            def __str__(self):
                return "value"

        html = self.widget.render("myfile", NoURLFieldFile())
        self.assertHTMLEqual(html, '<input name="myfile" type="file">')