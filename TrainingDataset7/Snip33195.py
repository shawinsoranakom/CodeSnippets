def test_urlencode01(self):
        output = self.engine.render_to_string("urlencode01", {"url": '/test&"/me?/'})
        self.assertEqual(output, "/test%26%22/me%3F/")