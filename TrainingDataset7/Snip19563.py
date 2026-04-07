def test_first_from_unordered_queryset_aggregation_pk_selected_separately(self):
        self.assertEqual(
            Comment.objects.values("tenant", "id").annotate(max=Max("id")).first(),
            {"tenant": self.comment_1.tenant_id, "id": 1, "max": 1},
        )