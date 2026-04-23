def test_repr_with_expressions(self):
        constraint = models.UniqueConstraint(
            Lower("title"),
            F("author"),
            name="book_func_uq",
        )
        self.assertEqual(
            repr(constraint),
            "<UniqueConstraint: expressions=(Lower(F(title)), F(author)) "
            "name='book_func_uq'>",
        )