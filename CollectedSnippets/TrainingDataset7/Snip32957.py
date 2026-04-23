def test_unicode(self):
        self.assertEqual(iriencode("S\xf8r-Tr\xf8ndelag"), "S%C3%B8r-Tr%C3%B8ndelag")