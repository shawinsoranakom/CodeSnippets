def test_condition_deeper_relation_name_implicit_exact(self):
        msg = (
            "FilteredRelation's condition doesn't support nested relations "
            "deeper than the relation_name (got 'book__editor__name' for 'book')."
        )
        with self.assertRaisesMessage(ValueError, msg):
            Author.objects.annotate(
                book_editor=FilteredRelation(
                    "book",
                    condition=Q(book__editor__name="b"),
                ),
            )