def test_escape(self):
        escaped = force_escape("<some html & special characters > here")
        self.assertEqual(escaped, "&lt;some html &amp; special characters &gt; here")
        self.assertIsInstance(escaped, SafeData)