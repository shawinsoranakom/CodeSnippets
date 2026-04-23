def test_dates_alias(self):
        qs = Book.objects.alias(
            pubdate_alias=F("pubdate"),
        ).dates("pubdate_alias", "month")
        self.assertCountEqual(
            qs,
            [
                datetime.date(1991, 10, 1),
                datetime.date(1995, 1, 1),
                datetime.date(2007, 12, 1),
                datetime.date(2008, 6, 1),
            ],
        )