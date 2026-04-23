def test_distinct_on_stringagg(self):
        books = Book.objects.aggregate(
            ratings=StringAgg(Cast(F("rating"), CharField()), Value(","), distinct=True)
        )
        self.assertCountEqual(books["ratings"].split(","), ["3", "4", "4.5", "5"])