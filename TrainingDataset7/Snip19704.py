def test_in_bulk_values_list_multiple_fields(self):
        result = Comment.objects.values_list("pk", "text").in_bulk([self.comment.pk])
        self.assertEqual(
            result, {self.comment.pk: (self.comment.pk, self.comment.text)}
        )