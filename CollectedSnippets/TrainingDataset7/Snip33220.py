def test_malformed(self):
        """
        #16395 - Check urlize doesn't highlight malformed URIs
        """
        self.assertEqual(urlize("http:///www.google.com"), "http:///www.google.com")
        self.assertEqual(urlize("http://.google.com"), "http://.google.com")
        self.assertEqual(urlize("http://@foo.com"), "http://@foo.com")