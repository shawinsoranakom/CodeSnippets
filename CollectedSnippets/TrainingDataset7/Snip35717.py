def test_converter_reverse(self):
        for expected, (url_name, app_name, kwargs) in converter_test_data:
            if app_name:
                url_name = "%s:%s" % (app_name, url_name)
            with self.subTest(url=url_name):
                url = reverse(url_name, kwargs=kwargs)
                self.assertEqual(url, expected)