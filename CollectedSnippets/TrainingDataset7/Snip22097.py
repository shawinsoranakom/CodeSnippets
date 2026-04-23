def test_nested_foreign_key_filtered_base_object(self):
        qs = (
            Author.objects.annotate(
                alice_editors=FilteredRelation(
                    "book__editor",
                    condition=Q(name="Alice"),
                ),
            )
            .values(
                "name",
                "alice_editors__pk",
            )
            .order_by("name", "alice_editors__name")
            .distinct()
        )
        self.assertSequenceEqual(
            qs,
            [
                {"name": self.author1.name, "alice_editors__pk": self.editor_a.pk},
                {"name": self.author2.name, "alice_editors__pk": None},
            ],
        )