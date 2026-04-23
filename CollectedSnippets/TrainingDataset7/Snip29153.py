def test_generic_key_separation(self):
        "Generic fields are constrained to a single database"
        # Create a book and author on the default database
        pro = Book.objects.create(
            title="Pro Django", published=datetime.date(2008, 12, 16)
        )
        review1 = Review.objects.create(source="Python Monthly", content_object=pro)

        # Create a book and author on the other database
        dive = Book.objects.using("other").create(
            title="Dive into Python", published=datetime.date(2009, 5, 4)
        )

        review2 = Review.objects.using("other").create(
            source="Python Weekly", content_object=dive
        )

        review1 = Review.objects.using("default").get(source="Python Monthly")
        self.assertEqual(review1.content_object.title, "Pro Django")

        review2 = Review.objects.using("other").get(source="Python Weekly")
        self.assertEqual(review2.content_object.title, "Dive into Python")

        # Reget the objects to clear caches
        dive = Book.objects.using("other").get(title="Dive into Python")

        # Retrieve related object by descriptor. Related objects should be
        # database-bound.
        self.assertEqual(
            list(dive.reviews.values_list("source", flat=True)), ["Python Weekly"]
        )