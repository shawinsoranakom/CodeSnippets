def test_escape_characters(self):
        self.assertEqual(date(datetime(2005, 12, 29), r"jS \o\f F"), "29th of December")