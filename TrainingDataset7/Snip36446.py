def test_http_date(self):
        t = 1167616461.0
        self.assertEqual(http_date(t), "Mon, 01 Jan 2007 01:54:21 GMT")