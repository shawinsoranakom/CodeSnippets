def test_even_more_aggregate(self):
        publishers = (
            Publisher.objects.annotate(
                earliest_book=Min("book__pubdate"),
            )
            .exclude(earliest_book=None)
            .order_by("earliest_book")
            .values(
                "earliest_book",
                "num_awards",
                "id",
                "name",
            )
        )
        self.assertEqual(
            list(publishers),
            [
                {
                    "earliest_book": datetime.date(1991, 10, 15),
                    "num_awards": 9,
                    "id": self.p4.id,
                    "name": "Morgan Kaufmann",
                },
                {
                    "earliest_book": datetime.date(1995, 1, 15),
                    "num_awards": 7,
                    "id": self.p3.id,
                    "name": "Prentice Hall",
                },
                {
                    "earliest_book": datetime.date(2007, 12, 6),
                    "num_awards": 3,
                    "id": self.p1.id,
                    "name": "Apress",
                },
                {
                    "earliest_book": datetime.date(2008, 3, 3),
                    "num_awards": 1,
                    "id": self.p2.id,
                    "name": "Sams",
                },
            ],
        )

        vals = Store.objects.aggregate(
            Max("friday_night_closing"), Min("original_opening")
        )
        self.assertEqual(
            vals,
            {
                "friday_night_closing__max": datetime.time(23, 59, 59),
                "original_opening__min": datetime.datetime(1945, 4, 25, 16, 24, 14),
            },
        )