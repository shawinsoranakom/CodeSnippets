def test_generic_key_reverse_operations(self):
        "Generic reverse manipulations are all constrained to a single DB"
        dive = Book.objects.using("other").create(
            title="Dive into Python", published=datetime.date(2009, 5, 4)
        )
        temp = Book.objects.using("other").create(
            title="Temp", published=datetime.date(2009, 5, 4)
        )
        review1 = Review.objects.using("other").create(
            source="Python Weekly", content_object=dive
        )
        review2 = Review.objects.using("other").create(
            source="Python Monthly", content_object=temp
        )

        self.assertEqual(
            list(
                Review.objects.using("default")
                .filter(object_id=dive.pk)
                .values_list("source", flat=True)
            ),
            [],
        )
        self.assertEqual(
            list(
                Review.objects.using("other")
                .filter(object_id=dive.pk)
                .values_list("source", flat=True)
            ),
            ["Python Weekly"],
        )

        # Add a second review
        dive.reviews.add(review2)
        self.assertEqual(
            list(
                Review.objects.using("default")
                .filter(object_id=dive.pk)
                .values_list("source", flat=True)
            ),
            [],
        )
        self.assertEqual(
            list(
                Review.objects.using("other")
                .filter(object_id=dive.pk)
                .values_list("source", flat=True)
            ),
            ["Python Monthly", "Python Weekly"],
        )

        # Remove the second author
        dive.reviews.remove(review1)
        self.assertEqual(
            list(
                Review.objects.using("default")
                .filter(object_id=dive.pk)
                .values_list("source", flat=True)
            ),
            [],
        )
        self.assertEqual(
            list(
                Review.objects.using("other")
                .filter(object_id=dive.pk)
                .values_list("source", flat=True)
            ),
            ["Python Monthly"],
        )

        # Clear all reviews
        dive.reviews.clear()
        self.assertEqual(
            list(
                Review.objects.using("default")
                .filter(object_id=dive.pk)
                .values_list("source", flat=True)
            ),
            [],
        )
        self.assertEqual(
            list(
                Review.objects.using("other")
                .filter(object_id=dive.pk)
                .values_list("source", flat=True)
            ),
            [],
        )

        # Create an author through the generic interface
        dive.reviews.create(source="Python Daily")
        self.assertEqual(
            list(
                Review.objects.using("default")
                .filter(object_id=dive.pk)
                .values_list("source", flat=True)
            ),
            [],
        )
        self.assertEqual(
            list(
                Review.objects.using("other")
                .filter(object_id=dive.pk)
                .values_list("source", flat=True)
            ),
            ["Python Daily"],
        )