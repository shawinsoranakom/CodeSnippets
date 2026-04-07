def test_composed_check_constraint_with_fk(self):
        constraint = CheckConstraint(
            condition=Q(author__gt=0), name="book_author_check"
        )
        self._test_composed_constraint_with_fk(constraint)