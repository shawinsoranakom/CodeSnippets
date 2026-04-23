def test_generic_key_cross_database_protection(self):
        """
        Operations that involve sharing generic key objects across databases
        raise an error.
        """
        # Create a book and author on the default database
        pro = Book.objects.create(
            title="Pro Django", published=datetime.date(2008, 12, 16)
        )
        review1 = Review.objects.create(source="Python Monthly", content_object=pro)

        # Create a book and author on the other database
        dive = Book.objects.using("other").create(
            title="Dive into Python", published=datetime.date(2009, 5, 4)
        )

        Review.objects.using("other").create(
            source="Python Weekly", content_object=dive
        )

        # Set a foreign key with an object from a different database
        msg = (
            'Cannot assign "<ContentType: Multiple_Database | book>": the '
            "current database router prevents this relation."
        )
        with self.assertRaisesMessage(ValueError, msg):
            review1.content_object = dive

        # Add to a foreign key set with an object from a different database
        msg = (
            "<Review: Python Monthly> instance isn't saved. "
            "Use bulk=False or save the object first."
        )
        with self.assertRaisesMessage(ValueError, msg):
            with transaction.atomic(using="other"):
                dive.reviews.add(review1)

        # BUT! if you assign a FK object when the base object hasn't
        # been saved yet, you implicitly assign the database for the
        # base object.
        review3 = Review(source="Python Daily")
        # initially, no db assigned
        self.assertIsNone(review3._state.db)

        # Dive comes from 'other', so review3 is set to use 'other'...
        review3.content_object = dive
        self.assertEqual(review3._state.db, "other")
        # ... but it isn't saved yet
        self.assertEqual(
            list(
                Review.objects.using("default")
                .filter(object_id=pro.pk)
                .values_list("source", flat=True)
            ),
            ["Python Monthly"],
        )
        self.assertEqual(
            list(
                Review.objects.using("other")
                .filter(object_id=dive.pk)
                .values_list("source", flat=True)
            ),
            ["Python Weekly"],
        )

        # When saved, John goes to 'other'
        review3.save()
        self.assertEqual(
            list(
                Review.objects.using("default")
                .filter(object_id=pro.pk)
                .values_list("source", flat=True)
            ),
            ["Python Monthly"],
        )
        self.assertEqual(
            list(
                Review.objects.using("other")
                .filter(object_id=dive.pk)
                .values_list("source", flat=True)
            ),
            ["Python Daily", "Python Weekly"],
        )