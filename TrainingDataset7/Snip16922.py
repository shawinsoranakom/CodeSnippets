def test_filtered_aggregate_on_exists(self):
        aggregate = Book.objects.values("publisher").aggregate(
            max_rating=Max(
                "rating",
                filter=Exists(
                    Book.authors.through.objects.filter(book=OuterRef("pk")),
                ),
            ),
        )
        self.assertEqual(aggregate, {"max_rating": 4.5})