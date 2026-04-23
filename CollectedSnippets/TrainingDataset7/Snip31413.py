def test_composed_constraint_with_fk(self):
        constraint = UniqueConstraint(
            fields=["author", "title"],
            name="book_author_title_uniq",
        )
        self._test_composed_constraint_with_fk(constraint)