def test_condition_outside_relation_name(self):
        msg = (
            "FilteredRelation's condition doesn't support relations outside "
            "the 'book__editor' (got 'book__author__name__icontains')."
        )
        with self.assertRaisesMessage(ValueError, msg):
            Author.objects.annotate(
                book_editor=FilteredRelation(
                    "book__editor",
                    condition=Q(book__author__name__icontains="book"),
                ),
            )