def test_unicode(self):
        # uppercase E umlaut
        self.assertEqual(lower("\xcb"), "\xeb")