def test_in_bulk_values_field(self):
        result = Comment.objects.values("text").in_bulk([self.comment.pk])
        self.assertEqual(
            result,
            {self.comment.pk: {"text": self.comment.text}},
        )