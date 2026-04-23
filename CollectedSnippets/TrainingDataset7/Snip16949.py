def test_distinct_on_stringagg_sqlite_special_case(self):
        """
        Value(",") is the only delimiter usable on SQLite with distinct=True.
        """
        books = Book.objects.aggregate(
            ratings=StringAgg(Cast(F("rating"), CharField()), Value(","), distinct=True)
        )
        self.assertCountEqual(books["ratings"].split(","), ["3.0", "4.0", "4.5", "5.0"])