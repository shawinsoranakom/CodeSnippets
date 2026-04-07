def test_forward_m2m_to_attr_conflict(self):
        msg = "to_attr=authors conflicts with a field on the Book model."
        authors = Author.objects.all()
        with self.assertRaisesMessage(ValueError, msg):
            list(
                Book.objects.prefetch_related(
                    Prefetch("authors", queryset=authors, to_attr="authors"),
                )
            )
        # Without the ValueError, an author was deleted due to the implicit
        # save of the relation assignment.
        self.assertEqual(self.book1.authors.count(), 3)