def test_eq_with_nulls_distinct(self):
        constraint_1 = models.UniqueConstraint(
            Lower("title"),
            nulls_distinct=False,
            name="book_func_nulls_distinct_uq",
        )
        constraint_2 = models.UniqueConstraint(
            Lower("title"),
            nulls_distinct=True,
            name="book_func_nulls_distinct_uq",
        )
        constraint_3 = models.UniqueConstraint(
            Lower("title"),
            name="book_func_nulls_distinct_uq",
        )
        self.assertEqual(constraint_1, constraint_1)
        self.assertEqual(constraint_1, mock.ANY)
        self.assertNotEqual(constraint_1, constraint_2)
        self.assertNotEqual(constraint_1, constraint_3)
        self.assertNotEqual(constraint_2, constraint_3)