def test_condition_spans_join(self):
        self.assertSequenceEqual(
            Book.objects.annotate(
                contains_editor_author=FilteredRelation(
                    "author", condition=Q(author__name__icontains=F("editor__name"))
                )
            ).filter(
                contains_editor_author__isnull=False,
            ),
            [self.book1],
        )