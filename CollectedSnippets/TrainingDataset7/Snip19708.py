def test_in_bulk_values_list_flat_tenant(self):
        result = Comment.objects.values_list("tenant", flat=True).in_bulk(
            [self.comment.pk]
        )
        self.assertEqual(result, {self.comment.pk: self.tenant.id})