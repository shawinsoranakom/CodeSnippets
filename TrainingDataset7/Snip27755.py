def test_textchoices_containment(self):
        self.assertIn(YearInSchool.FRESHMAN, YearInSchool)
        self.assertIn("FR", YearInSchool)
        self.assertNotIn("XX", YearInSchool)