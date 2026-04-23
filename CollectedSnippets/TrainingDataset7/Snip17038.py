def test_group_by_transform_column(self):
        self.assertSequenceEqual(
            Store.objects.values(
                "original_opening__date",
                "name",
            )
            .annotate(Count("books"))
            .order_by("name"),
            [
                {
                    "original_opening__date": datetime.date(1994, 4, 23),
                    "name": "Amazon.com",
                    "books__count": 6,
                },
                {
                    "original_opening__date": datetime.date(2001, 3, 15),
                    "name": "Books.com",
                    "books__count": 4,
                },
                {
                    "original_opening__date": datetime.date(1945, 4, 25),
                    "name": "Mamma and Pappa's Books",
                    "books__count": 3,
                },
            ],
        )