def test_with_condition_as_expression_error(self):
        msg = "condition argument must be a Q() instance."
        expression = Case(
            When(book__title__iexact="poem by alice", then=True),
            default=False,
        )
        with self.assertRaisesMessage(ValueError, msg):
            FilteredRelation("book", condition=expression)