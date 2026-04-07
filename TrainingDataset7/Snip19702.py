def test_in_bulk_values_fields(self):
        result = Comment.objects.values("pk", "text").in_bulk([self.comment.pk])
        self.assertEqual(
            result,
            {self.comment.pk: {"pk": self.comment.pk, "text": self.comment.text}},
        )