def test_am_pm(self):
        morning = time(7, 00)
        evening = time(19, 00)
        self.assertEqual(dateformat.format(morning, "a"), "a.m.")
        self.assertEqual(dateformat.format(evening, "a"), "p.m.")
        self.assertEqual(dateformat.format(morning, "A"), "AM")
        self.assertEqual(dateformat.format(evening, "A"), "PM")