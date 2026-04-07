def test_path_trailing_newlines(self):
        tests = [
            "/articles/2003/\n",
            "/articles/2010/\n",
            "/en/foo/\n",
            "/included_urls/extra/\n",
            "/regex/1/\n",
            "/users/1/\n",
        ]
        for url in tests:
            with self.subTest(url=url), self.assertRaises(Resolver404):
                resolve(url)