def test_generic_key_deletion(self):
        """
        Cascaded deletions of Generic Key relations issue queries on the right
        database.
        """
        dive = Book.objects.using("other").create(
            title="Dive into Python", published=datetime.date(2009, 5, 4)
        )
        Review.objects.using("other").create(
            source="Python Weekly", content_object=dive
        )

        # Check the initial state
        self.assertEqual(Book.objects.using("default").count(), 0)
        self.assertEqual(Review.objects.using("default").count(), 0)

        self.assertEqual(Book.objects.using("other").count(), 1)
        self.assertEqual(Review.objects.using("other").count(), 1)

        # Delete the Book object, which will cascade onto the pet
        dive.delete(using="other")

        self.assertEqual(Book.objects.using("default").count(), 0)
        self.assertEqual(Review.objects.using("default").count(), 0)

        # Both the pet and the person have been deleted from the right database
        self.assertEqual(Book.objects.using("other").count(), 0)
        self.assertEqual(Review.objects.using("other").count(), 0)