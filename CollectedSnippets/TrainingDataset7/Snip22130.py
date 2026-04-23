def test_condition_self_ref(self):
        self.assertSequenceEqual(
            Book.objects.annotate(
                contains_author=FilteredRelation(
                    "author",
                    condition=Q(title__icontains=F("author__name")),
                )
            ).filter(
                contains_author__isnull=False,
            ),
            [self.book1],
        )