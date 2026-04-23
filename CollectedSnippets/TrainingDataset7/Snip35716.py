def test_converter_resolve(self):
        for url, (url_name, app_name, kwargs) in converter_test_data:
            with self.subTest(url=url):
                match = resolve(url)
                self.assertEqual(match.url_name, url_name)
                self.assertEqual(match.app_name, app_name)
                self.assertEqual(match.kwargs, kwargs)