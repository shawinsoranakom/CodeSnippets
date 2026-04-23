def test_select_related(self):
        """
        Database assignment is retained if an object is retrieved with
        select_related().
        """
        # Create a book and author on the other database
        mark = Person.objects.using("other").create(name="Mark Pilgrim")
        Book.objects.using("other").create(
            title="Dive into Python",
            published=datetime.date(2009, 5, 4),
            editor=mark,
        )

        # Retrieve the Person using select_related()
        book = (
            Book.objects.using("other")
            .select_related("editor")
            .get(title="Dive into Python")
        )

        # The editor instance should have a db state
        self.assertEqual(book.editor._state.db, "other")