def test_relation_name_lookup(self):
        msg = (
            "FilteredRelation's relation_name cannot contain lookups (got "
            "'book__title__icontains')."
        )
        with self.assertRaisesMessage(ValueError, msg):
            Author.objects.annotate(
                book_title=FilteredRelation(
                    "book__title__icontains",
                    condition=Q(book__title="Poem by Alice"),
                ),
            )