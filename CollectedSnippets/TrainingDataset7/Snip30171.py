def test_reverse_m2m_to_attr_conflict(self):
        msg = "to_attr=books conflicts with a field on the Author model."
        poems = Book.objects.filter(title="Poems")
        with self.assertRaisesMessage(ValueError, msg):
            list(
                Author.objects.prefetch_related(
                    Prefetch("books", queryset=poems, to_attr="books"),
                )
            )
        # Without the ValueError, a book was deleted due to the implicit
        # save of reverse relation assignment.
        self.assertEqual(self.author1.books.count(), 2)