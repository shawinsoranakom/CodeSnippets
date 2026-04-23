def test_view_calls_subview(self):
        url = "/subview_calling_view/?%s" % urlencode({"url": self.live_server_url})
        with self.urlopen(url) as f:
            self.assertEqual(f.read(), b"subview calling view: subview")