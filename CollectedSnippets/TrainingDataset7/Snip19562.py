def test_first_from_unordered_queryset_aggregation_pk_selected(self):
        self.assertEqual(
            Comment.objects.values("pk").annotate(max=Max("id")).first(),
            {"pk": (self.comment_1.tenant_id, 1), "max": 1},
        )