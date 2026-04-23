def test_in_bulk_values_list_flat(self):
        result = Comment.objects.values_list("text", flat=True).in_bulk(
            [self.comment.pk]
        )
        self.assertEqual(result, {self.comment.pk: self.comment.text})