def test_remove_ignored_unique_constraint_not_create_fk_index(self):
        with connection.schema_editor() as editor:
            editor.create_model(Author)
            editor.create_model(Book)
        constraint = UniqueConstraint(
            "author",
            condition=Q(title__in=["tHGttG", "tRatEotU"]),
            name="book_author_condition_uniq",
        )
        # Add unique constraint.
        with connection.schema_editor() as editor:
            editor.add_constraint(Book, constraint)
        old_constraints = self.get_constraints_for_column(
            Book,
            Book._meta.get_field("author").column,
        )
        # Remove unique constraint.
        with connection.schema_editor() as editor:
            editor.remove_constraint(Book, constraint)
        new_constraints = self.get_constraints_for_column(
            Book,
            Book._meta.get_field("author").column,
        )
        # Redundant foreign key index is not added.
        self.assertEqual(
            (
                len(old_constraints) - 1
                if connection.features.supports_partial_indexes
                else len(old_constraints)
            ),
            len(new_constraints),
        )