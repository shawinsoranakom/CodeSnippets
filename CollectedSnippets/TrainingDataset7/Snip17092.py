def test_select_related(self):
        # Regression for #10064: select_related() plays nice with aggregates
        obj = (
            Book.objects.select_related("publisher")
            .annotate(num_authors=Count("authors"))
            .values()
            .get(isbn="013790395")
        )
        self.assertEqual(
            obj,
            {
                "contact_id": self.a8.id,
                "id": self.b5.id,
                "isbn": "013790395",
                "name": "Artificial Intelligence: A Modern Approach",
                "num_authors": 2,
                "pages": 1132,
                "price": Decimal("82.8"),
                "pubdate": datetime.date(1995, 1, 15),
                "publisher_id": self.p3.id,
                "rating": 4.0,
            },
        )