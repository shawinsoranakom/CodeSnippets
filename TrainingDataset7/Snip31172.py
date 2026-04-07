def test_unicode_cookie(self):
        """HttpResponse.set_cookie() works with Unicode data."""
        response = HttpResponse()
        cookie_value = "清風"
        response.set_cookie("test", cookie_value)
        self.assertEqual(response.cookies["test"].value, cookie_value)