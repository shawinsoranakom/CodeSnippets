def test_save_clears_annotations_from_base_manager(self):
        """Model.save() clears annotations from the base manager."""
        self.assertEqual(Book._meta.base_manager.name, "annotated_objects")
        book = Book.annotated_objects.create(title="Hunting")
        Person.objects.create(
            first_name="Bugs",
            last_name="Bunny",
            fun=True,
            favorite_book=book,
            favorite_thing_id=1,
        )
        book = Book.annotated_objects.first()
        self.assertEqual(book.favorite_avg, 1)  # Annotation from the manager.
        book.title = "New Hunting"
        # save() fails if annotations that involve related fields aren't
        # cleared before the update query.
        book.save()
        self.assertEqual(Book.annotated_objects.first().title, "New Hunting")