def test_l10n_invalid_date_in(self):
        # Invalid dates shouldn't be allowed
        a = GetDate({"mydate_month": "2", "mydate_day": "31", "mydate_year": "2010"})
        self.assertFalse(a.is_valid())
        # 'Geef een geldige datum op.' = 'Enter a valid date.'
        self.assertEqual(a.errors, {"mydate": ["Voer een geldige datum in."]})