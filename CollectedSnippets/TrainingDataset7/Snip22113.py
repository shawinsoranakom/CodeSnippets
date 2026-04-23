def test_eq(self):
        self.assertEqual(
            FilteredRelation("book", condition=Q(book__title="b")), mock.ANY
        )