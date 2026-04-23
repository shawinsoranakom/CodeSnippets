def test_generic_key_cross_database_protection(self):
        "Generic Key operations can span databases if they share a source"
        # Create a book and author on the default database
        pro = Book.objects.using("default").create(
            title="Pro Django", published=datetime.date(2008, 12, 16)
        )

        review1 = Review.objects.using("default").create(
            source="Python Monthly", content_object=pro
        )

        # Create a book and author on the other database
        dive = Book.objects.using("other").create(
            title="Dive into Python", published=datetime.date(2009, 5, 4)
        )

        review2 = Review.objects.using("other").create(
            source="Python Weekly", content_object=dive
        )

        # Set a generic foreign key with an object from a different database
        review1.content_object = dive

        # Database assignments of original objects haven't changed...
        self.assertEqual(pro._state.db, "default")
        self.assertEqual(review1._state.db, "default")
        self.assertEqual(dive._state.db, "other")
        self.assertEqual(review2._state.db, "other")

        # ... but they will when the affected object is saved.
        dive.save()
        self.assertEqual(review1._state.db, "default")
        self.assertEqual(dive._state.db, "default")

        # ...and the source database now has a copy of any object saved
        Book.objects.using("default").get(title="Dive into Python").delete()

        # This isn't a real primary/replica database, so restore the original
        # from other
        dive = Book.objects.using("other").get(title="Dive into Python")
        self.assertEqual(dive._state.db, "other")

        # Add to a generic foreign key set with an object from a different
        # database
        dive.reviews.add(review1)

        # Database assignments of original objects haven't changed...
        self.assertEqual(pro._state.db, "default")
        self.assertEqual(review1._state.db, "default")
        self.assertEqual(dive._state.db, "other")
        self.assertEqual(review2._state.db, "other")

        # ... but they will when the affected object is saved.
        dive.save()
        self.assertEqual(dive._state.db, "default")

        # ...and the source database now has a copy of any object saved
        Book.objects.using("default").get(title="Dive into Python").delete()

        # BUT! if you assign a FK object when the base object hasn't
        # been saved yet, you implicitly assign the database for the
        # base object.
        review3 = Review(source="Python Daily")
        # initially, no db assigned
        self.assertIsNone(review3._state.db)

        # Dive comes from 'other', so review3 is set to use the source of
        # 'other'...
        review3.content_object = dive
        self.assertEqual(review3._state.db, "default")

        # If you create an object through a M2M relation, it will be
        # written to the write database, even if the original object
        # was on the read database
        dive = Book.objects.using("other").get(title="Dive into Python")
        nyt = dive.reviews.create(source="New York Times", content_object=dive)
        self.assertEqual(nyt._state.db, "default")