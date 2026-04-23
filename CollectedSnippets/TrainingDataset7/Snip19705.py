def test_in_bulk_values_list_fields_are_pk(self):
        result = Comment.objects.values_list("tenant", "id").in_bulk([self.comment.pk])
        self.assertEqual(
            result, {self.comment.pk: (self.comment.tenant_id, self.comment.id)}
        )