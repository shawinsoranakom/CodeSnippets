def test_redirect_repr(self):
        response = HttpResponseRedirect("/redirected/")
        expected = (
            '<HttpResponseRedirect status_code=302, "text/html; charset=utf-8", '
            'url="/redirected/">'
        )
        self.assertEqual(repr(response), expected)