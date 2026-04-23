def test_in_bulk_values_list(self):
        result = Comment.objects.values_list("text").in_bulk([self.comment.pk])
        self.assertEqual(result, {self.comment.pk: (self.comment.text,)})