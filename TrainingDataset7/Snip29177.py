def test_subquery(self):
        """Make sure as_sql works with subqueries and primary/replica."""
        # Create a book and author on the other database

        mark = Person.objects.using("other").create(name="Mark Pilgrim")
        Book.objects.using("other").create(
            title="Dive into Python",
            published=datetime.date(2009, 5, 4),
            editor=mark,
        )

        sub = Person.objects.filter(name="Mark Pilgrim")
        qs = Book.objects.filter(editor__in=sub)

        # When you call __str__ on the query object, it doesn't know about
        # using so it falls back to the default. Don't let routing instructions
        # force the subquery to an incompatible database.
        str(qs.query)

        # If you evaluate the query, it should work, running on 'other'
        self.assertEqual(list(qs.values_list("title", flat=True)), ["Dive into Python"])