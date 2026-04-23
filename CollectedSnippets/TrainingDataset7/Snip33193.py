def test_unicode(self):
        # lowercase e umlaut
        self.assertEqual(upper("\xeb"), "\xcb")