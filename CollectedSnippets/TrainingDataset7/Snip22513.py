def test_form_field(self):
        a = GetDate({"mydate_month": "4", "mydate_day": "1", "mydate_year": "2008"})
        self.assertTrue(a.is_valid())
        self.assertEqual(a.cleaned_data["mydate"], date(2008, 4, 1))

        # As with any widget that implements get_value_from_datadict(), we must
        # accept the input from the "as_hidden" rendering as well.
        self.assertHTMLEqual(
            a["mydate"].as_hidden(),
            '<input type="hidden" name="mydate" value="2008-04-01" id="id_mydate">',
        )

        b = GetDate({"mydate": "2008-4-1"})
        self.assertTrue(b.is_valid())
        self.assertEqual(b.cleaned_data["mydate"], date(2008, 4, 1))

        # Invalid dates shouldn't be allowed
        c = GetDate({"mydate_month": "2", "mydate_day": "31", "mydate_year": "2010"})
        self.assertFalse(c.is_valid())
        self.assertEqual(c.errors, {"mydate": ["Enter a valid date."]})

        # label tag is correctly associated with month dropdown
        d = GetDate({"mydate_month": "1", "mydate_day": "1", "mydate_year": "2010"})
        self.assertIn('<label for="id_mydate_month">', d.as_p())

        # Inputs raising an OverflowError.
        e = GetDate(
            {
                "mydate_month": str(sys.maxsize + 1),
                "mydate_day": "31",
                "mydate_year": "2010",
            }
        )
        self.assertIs(e.is_valid(), False)
        self.assertEqual(e.errors, {"mydate": ["Enter a valid date."]})