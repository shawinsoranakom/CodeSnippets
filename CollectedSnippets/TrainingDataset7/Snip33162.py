def test_truncate_unicode(self):
        self.assertEqual(
            truncatewords_html("\xc5ngstr\xf6m was here", 1), "\xc5ngstr\xf6m …"
        )