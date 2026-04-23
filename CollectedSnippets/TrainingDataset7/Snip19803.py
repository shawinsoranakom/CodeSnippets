def test_eq_with_expressions(self):
        constraint = models.UniqueConstraint(
            Lower("title"),
            F("author"),
            name="book_func_uq",
        )
        same_constraint = models.UniqueConstraint(
            Lower("title"),
            "author",
            name="book_func_uq",
        )
        another_constraint = models.UniqueConstraint(
            Lower("title"),
            name="book_func_uq",
        )
        self.assertEqual(constraint, same_constraint)
        self.assertEqual(constraint, mock.ANY)
        self.assertNotEqual(constraint, another_constraint)