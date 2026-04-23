def test_environ(self):
        with self.urlopen("/environ_view/?%s" % urlencode({"q": "тест"})) as f:
            self.assertIn(b"QUERY_STRING: 'q=%D1%82%D0%B5%D1%81%D1%82'", f.read())