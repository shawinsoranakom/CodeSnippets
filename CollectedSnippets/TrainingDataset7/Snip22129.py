def test_condition_spans_join_chained(self):
        self.assertSequenceEqual(
            Book.objects.annotate(
                contains_editor_author=FilteredRelation(
                    "author", condition=Q(author__name__icontains=F("editor__name"))
                ),
                contains_editor_author_ref=FilteredRelation(
                    "author",
                    condition=Q(author__name=F("contains_editor_author__name")),
                ),
            ).filter(
                contains_editor_author_ref__isnull=False,
            ),
            [self.book1],
        )