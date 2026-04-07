def test_l10n_date_changed(self):
        """
        DateField.has_changed() with SelectDateWidget works with a localized
        date format (#17165).
        """
        # With Field.show_hidden_initial=False
        b = GetDate(
            {
                "mydate_year": "2008",
                "mydate_month": "4",
                "mydate_day": "1",
            },
            initial={"mydate": date(2008, 4, 1)},
        )
        self.assertFalse(b.has_changed())

        b = GetDate(
            {
                "mydate_year": "2008",
                "mydate_month": "4",
                "mydate_day": "2",
            },
            initial={"mydate": date(2008, 4, 1)},
        )
        self.assertTrue(b.has_changed())

        # With Field.show_hidden_initial=True
        class GetDateShowHiddenInitial(Form):
            mydate = DateField(widget=SelectDateWidget, show_hidden_initial=True)

        b = GetDateShowHiddenInitial(
            {
                "mydate_year": "2008",
                "mydate_month": "4",
                "mydate_day": "1",
                "initial-mydate": HiddenInput().format_value(date(2008, 4, 1)),
            },
            initial={"mydate": date(2008, 4, 1)},
        )
        self.assertFalse(b.has_changed())

        b = GetDateShowHiddenInitial(
            {
                "mydate_year": "2008",
                "mydate_month": "4",
                "mydate_day": "22",
                "initial-mydate": HiddenInput().format_value(date(2008, 4, 1)),
            },
            initial={"mydate": date(2008, 4, 1)},
        )
        self.assertTrue(b.has_changed())

        b = GetDateShowHiddenInitial(
            {
                "mydate_year": "2008",
                "mydate_month": "4",
                "mydate_day": "22",
                "initial-mydate": HiddenInput().format_value(date(2008, 4, 1)),
            },
            initial={"mydate": date(2008, 4, 22)},
        )
        self.assertTrue(b.has_changed())

        b = GetDateShowHiddenInitial(
            {
                "mydate_year": "2008",
                "mydate_month": "4",
                "mydate_day": "22",
                "initial-mydate": HiddenInput().format_value(date(2008, 4, 22)),
            },
            initial={"mydate": date(2008, 4, 1)},
        )
        self.assertFalse(b.has_changed())