def test_incompatible_iso_week_format_view(self):
        msg = (
            "ISO week directive '%V' is incompatible with the year directive "
            "'%Y'. Use the ISO year '%G' instead."
        )
        with self.assertRaisesMessage(ValueError, msg):
            self.client.get("/dates/books/2008/week/40/invalid_iso_week_year_format/")