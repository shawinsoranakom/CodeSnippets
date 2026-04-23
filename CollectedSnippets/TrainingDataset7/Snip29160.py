def test_subquery(self):
        """Make sure as_sql works with subqueries and primary/replica."""
        sub = Person.objects.using("other").filter(name="fff")
        qs = Book.objects.filter(editor__in=sub)

        # When you call __str__ on the query object, it doesn't know about
        # using so it falls back to the default. If the subquery explicitly
        # uses a different database, an error should be raised.
        msg = (
            "Subqueries aren't allowed across different databases. Force the "
            "inner query to be evaluated using `list(inner_query)`."
        )
        with self.assertRaisesMessage(ValueError, msg):
            str(qs.query)

        # Evaluating the query shouldn't work, either
        with self.assertRaisesMessage(ValueError, msg):
            for obj in qs:
                pass